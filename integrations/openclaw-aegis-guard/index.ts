const plugin = {
  id: "aegis-guard",
  name: "Aegis Guard",
  description: "Guardrail sidecar — inspects user prompts, LLM responses, and tool calls via Aegis.",
  register(api: any) {
    const cfg = (api.pluginConfig || {}) as Record<string, unknown>;

    const toBool = (v: unknown, fallback: boolean): boolean => {
      if (v === undefined || v === null) return fallback;
      if (typeof v === "boolean") return v;
      const s = String(v).trim().toLowerCase();
      if (["1", "true", "yes", "y", "on"].includes(s)) return true;
      if (["0", "false", "no", "n", "off", ""].includes(s)) return false;
      return fallback;
    };

    const aegisUrl = String(cfg.aegisUrl || "http://127.0.0.1:8000/v1").replace(/\/+$/, "");
    const environment = String(cfg.environment || "dev");
    const agentType = String(cfg.agentType || "general");
    const enforceInputGate = toBool(cfg.enforceInputGate, true);
    const enforceOutputGate = toBool(cfg.enforceOutputGate, true);
    const enforceToolGate = toBool(cfg.enforceToolGate, true);

    // -----------------------------------------------------------------------
    // State
    // -----------------------------------------------------------------------

    /** local key → Aegis session_id */
    const sessionMap = new Map<string, string>();
    /** trace_id from guard/input, passed to guard/output to link traces */
    const pendingTraceIds = new Map<string, string>();
    /** sessions where llm_output already ran guard/output (skip in message_sending) */
    const guardedOutputTurns = new Set<string>();
    /** sessions where input was blocked — force refusal on LLM response */
    const inputBlockedSessions = new Set<string>();
    /** block reason per session, set alongside inputBlockedSessions */
    const inputBlockedReasons = new Map<string, string>();
    /** refusal message to deliver in message_sending for blocked-input turns */
    const inputBlockedReplace = new Map<string, string>();

    // -----------------------------------------------------------------------
    // HTTP helpers
    // -----------------------------------------------------------------------

    async function post(path: string, body: Record<string, unknown>): Promise<any> {
      const res = await fetch(`${aegisUrl}${path}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Aegis ${path} → ${res.status}: ${txt.slice(0, 200)}`);
      }
      return res.json();
    }

    // -----------------------------------------------------------------------
    // Session key helpers — derive a stable string key from OpenClaw context
    // -----------------------------------------------------------------------

    function safe(v: unknown): string {
      const s = String(v ?? "").trim();
      return s && s !== "undefined" && s !== "null" ? s : "";
    }

    function dedupeKeys(parts: string[]): string[] {
      const seen = new Set<string>();
      const out: string[] = [];
      for (const p of parts) {
        if (p && !seen.has(p)) { seen.add(p); out.push(p); }
      }
      return out;
    }

    function llmKey(event: any, ctx: any): string {
      const parts = dedupeKeys([
        safe(ctx?.sessionKey),
        safe(event?.sessionId),
        safe(ctx?.sessionId),
        safe(event?.runId),
        safe(ctx?.runId),
        safe(ctx?.conversationId),
        safe(ctx?.messageThreadId),
        safe(ctx?.channelId),
        safe(ctx?.accountId),
      ]);
      return parts.length ? parts.join(":") : "openclaw-llm";
    }

    function toolKey(ctx: any): string {
      const parts = dedupeKeys([
        safe(ctx?.sessionKey),
        safe(ctx?.sessionId),
        safe(ctx?.conversationId),
        safe(ctx?.messageThreadId),
        safe(ctx?.channelId),
        safe(ctx?.accountId),
        safe(ctx?.to) || safe(ctx?.from),
      ]);
      return parts.length ? `tool:${parts.join(":")}` : "tool:openclaw";
    }

    function msgKey(ctx: any): string {
      const channel = safe(ctx?.channelId) || safe(ctx?.channel) || "unknown";
      const account = safe(ctx?.accountId) || "default";
      const conv = safe(ctx?.conversationId) || safe(ctx?.messageThreadId) || "default";
      return `msg:${channel}:${account}:${conv}`;
    }

    function allKeys(event: any, ctx: any): string[] {
      return dedupeKeys([
        `llm:${llmKey(event, ctx)}`,
        msgKey(ctx),
        toolKey(ctx),
        safe(event?.runId) ? `run:${safe(event?.runId)}` : "",
        safe(event?.sessionId) ? `sid:${safe(event?.sessionId)}` : "",
        safe(ctx?.sessionKey) ? `sk:${safe(ctx?.sessionKey)}` : "",
      ]);
    }

    // -----------------------------------------------------------------------
    // Session management
    // -----------------------------------------------------------------------

    async function createSession(): Promise<string> {
      const r = await post("/sessions", { agent_type: agentType, environment });
      const sid = String(r?.session_id || "");
      if (!sid) throw new Error("Aegis returned empty session_id");
      return sid;
    }

    function bindKeys(sid: string, keys: string[]): void {
      for (const k of dedupeKeys(keys)) sessionMap.set(k, sid);
    }

    async function resolveSession(event: any, ctx: any, preferredKey?: string): Promise<string> {
      const keys = dedupeKeys([preferredKey || "", ...allKeys(event, ctx)]);
      for (const k of keys) {
        const sid = sessionMap.get(k);
        if (sid) { bindKeys(sid, keys); return sid; }
      }
      const sid = await createSession();
      bindKeys(sid, keys);
      return sid;
    }

    /** Look up an existing session without creating one. Returns null if none found. */
    function findSession(event: any, ctx: any, preferredKey?: string): string | null {
      const keys = dedupeKeys([preferredKey || "", ...allKeys(event, ctx)]);
      for (const k of keys) {
        const sid = sessionMap.get(k);
        if (sid) { bindKeys(sid, keys); return sid; }
      }
      return null;
    }

    function bind(sid: string, event: any, ctx: any): void {
      bindKeys(sid, allKeys(event, ctx));
    }

    // -----------------------------------------------------------------------
    // Text extraction from OpenClaw event shapes
    // -----------------------------------------------------------------------

    function extractText(value: unknown): string {
      if (typeof value === "string") return value;
      if (Array.isArray(value)) return value.map(extractText).filter(Boolean).join("\n");
      if (value && typeof value === "object") {
        const o = value as Record<string, unknown>;
        const type = String(o.type || "").toLowerCase();
        if ((type === "text" || !type) && typeof o.text === "string") return o.text;
        if (typeof o.content === "string") return o.content;
        if (Array.isArray(o.content)) return extractText(o.content);
        if (typeof o.value === "string") return o.value;
      }
      return "";
    }

    function latestUserMessage(messages: unknown): string {
      if (!Array.isArray(messages)) return "";
      for (let i = messages.length - 1; i >= 0; i--) {
        const m = messages[i] as Record<string, unknown>;
        if (!m) continue;
        const role = String(m.role || m.type || "").toLowerCase();
        if (role !== "user") continue;
        const text = extractText(m.content).trim();
        if (text) return text;
      }
      return "";
    }

    function stripEnvelope(text: string): string {
      return text
        .replace(/^Safety note:\s*Use this sanitized request text as authoritative user intent:\s*/i, "")
        .replace(/^Sender \(untrusted metadata\):\s*```json[\s\S]*?```\s*/i, "")
        .replace(/^\[[^\]]+\]\s*/, "")
        .trim();
    }

    function userIntent(event: any): string {
      const prompt = String(event?.prompt || "").trim();
      const fromMessages = latestUserMessage(event?.messages);
      const raw = prompt || fromMessages;
      return stripEnvelope(raw) || raw;
    }

    // -----------------------------------------------------------------------
    // OpenClaw startup detection
    // -----------------------------------------------------------------------

    /** Bootstrap file reads on session start — skip guard to avoid noise */
    function isBootstrapRead(toolName: string, toolArgs: Record<string, unknown>): boolean {
      const name = toolName.trim().toLowerCase();
      if (!["read", "filesystem_read"].includes(name)) return false;
      const path = String(toolArgs.file_path || toolArgs.path || toolArgs.from || "").toLowerCase();
      return path.includes("/.openclaw/workspace/") &&
        /(soul\.md|user\.md|memory\.md|identity\.md|bootstrap\.md)$/.test(path);
    }

    /** Startup prompts OpenClaw sends internally — skip guard */
    function isStartupPrompt(text: string): boolean {
      return /\bA new session was started via \/new or \/reset\./i.test(text) ||
        /^based on this conversation,\s*generate.*filename slug/i.test(text);
    }

    function assistantText(event: any, texts: string[]): string {
      const direct = texts.map(v => String(v ?? "")).filter(v => v.trim()).join("\n\n");
      if (direct.trim()) return direct;
      for (const src of [event?.assistantMessage?.content, event?.content, event?.message?.content]) {
        const t = extractText(src).trim();
        if (t) return t;
      }
      return "";
    }

    // -----------------------------------------------------------------------
    // Hooks
    // -----------------------------------------------------------------------

    /**
     * On reset: clear session bindings so the next guard call starts a fresh
     * Aegis session. We do NOT eagerly create one here — that produces empty
     * sessions if no guard calls follow (e.g. startup-only sessions).
     */
    api.on("before_reset", (_event: any, _ctx: any) => {
      // Clear all state — after a /new or /reset the next session starts completely fresh.
      // Targeted key deletion is unreliable because the reset ctx may have different keys
      // than those stored from prior tool/llm hooks.
      sessionMap.clear();
      pendingTraceIds.clear();
      guardedOutputTurns.clear();
      inputBlockedSessions.clear();
      inputBlockedReasons.clear();
      inputBlockedReplace.clear();
      api.logger.info("[aegis-guard] all session state cleared on reset");
    });

    /** INPUT GATE — inspect user prompt before the LLM call */
    api.on("before_prompt_build", async (event: any, ctx: any) => {
      if (!enforceInputGate) return undefined;
      try {
        const content = userIntent(event);
        if (!content) return undefined;
        if (isStartupPrompt(content)) return undefined;

        const sid = await resolveSession(event, ctx, `llm:${llmKey(event, ctx)}`);
        bind(sid, event, ctx);

        const result = await post(`/sessions/${sid}/guard/input`, {
          content,
          metadata: { source: "openclaw-plugin", hook: "before_prompt_build", environment },
        });

        if (result?.trace_id) pendingTraceIds.set(sid, String(result.trace_id));

        if (result?.blocked) {
          const reason = String(result?.block_reason || "safety policy violation");
          api.logger.warn(`[aegis-guard] input blocked sid=${sid} score=${result?.scores?.final ?? "?"} reason=${reason}`);
          // Flag this session so llm_output skips the output gate — the LLM's
          // refusal naturally contains override-like language which triggers false positives.
          inputBlockedSessions.add(sid);
          inputBlockedReasons.set(sid, reason);
          return {
            systemPrompt: `You are a helpful and safe AI assistant. The user's latest message was automatically intercepted and blocked by a security guardrail. Reason: ${reason}. Without repeating the flagged content or revealing internal system details, respond in 1–2 sentences explaining naturally that you're unable to process that kind of request and why.`,
          };
        }
      } catch (err) {
        api.logger.warn(`[aegis-guard] before_prompt_build: ${String(err)}`);
      }
      return undefined;
    });

    /** TOOL GATE — inspect tool call args before execution */
    api.on("before_tool_call", async (event: any, ctx: any) => {
      if (!enforceToolGate) return undefined;
      try {
        const toolName = String(event?.toolName || "");
        const toolArgs = (event?.params || {}) as Record<string, unknown>;

        // Skip bootstrap reads — these are OpenClaw startup internals, not user-driven
        if (isBootstrapRead(toolName, toolArgs)) return undefined;

        // Only gate tool calls within an existing session (created by before_prompt_build).
        // Tool calls before any user prompt are internal OpenClaw operations — skip them.
        const sid = findSession(event, ctx, `tool:${toolKey(ctx)}`);
        if (!sid) return undefined;
        bind(sid, event, ctx);

        // If the current turn's input was blocked, halt all tool calls immediately.
        // The LLM cannot be stopped from running but it will not be allowed to act.
        if (inputBlockedSessions.has(sid)) {
          const reason = inputBlockedReasons.get(sid) || "safety policy violation";
          api.logger.warn(`[aegis-guard] tool call suppressed (input blocked) tool=${toolName} sid=${sid}`);
          return { block: true, blockReason: `This request was blocked by the security guardrail (reason: ${reason}). No tool calls are permitted.` };
        }

        const result = await post(`/sessions/${sid}/guard/tool`, {
          tool_name: toolName,
          tool_args: toolArgs,
          metadata: { source: "openclaw-plugin", hook: "before_tool_call", environment },
        });

        if (result?.blocked) {
          const reason = String(result?.block_reason || "safety policy violation");
          api.logger.warn(`[aegis-guard] tool blocked tool=${toolName} sid=${sid} reason=${reason}`);
          // blockReason is injected as a tool result by OpenClaw — the LLM sees it
          // and generates a natural explanation without us needing to override anything.
          return { block: true, blockReason: `Aegis safety gate blocked this tool call. Reason: ${reason}` };
        }
      } catch (err) {
        api.logger.warn(`[aegis-guard] before_tool_call: ${String(err)}`);
      }
      return undefined;
    });

    /** OUTPUT GATE — inspect LLM response before it reaches the user */
    api.on("llm_output", async (event: any, ctx: any) => {
      if (!enforceOutputGate) return;
      try {
        const assistantTexts: string[] = Array.isArray(event?.assistantTexts)
          ? event.assistantTexts
          : [];

        const content = assistantText(event, assistantTexts);
        if (!content.trim()) return;

        // Skip internal/startup turns — nothing useful to inspect
        const prompt = String(event?.prompt || "");
        if (isStartupPrompt(prompt) || isStartupPrompt(content)) return;

        // Only gate output within an existing session — greetings and internal LLM
        // responses that have no corresponding user prompt should not create sessions.
        const sid = findSession(event, ctx, `llm:${llmKey(event, ctx)}`);
        if (!sid) return;
        bind(sid, event, ctx);

        const traceId = pendingTraceIds.get(sid);
        if (traceId) pendingTraceIds.delete(sid);

        // If input was blocked, the LLM may have ignored the override system prompt.
        // Store a hardcoded refusal for message_sending to deliver, and record the
        // output trace as trusted (skip classification — refusal language trips detectors).
        if (inputBlockedSessions.has(sid)) {
          const blockReason = inputBlockedReasons.get(sid) || "safety policy violation";
          inputBlockedSessions.delete(sid);
          inputBlockedReasons.delete(sid);
          const refusal = `I'm unable to process that request — it was blocked by the security guardrail (reason: ${blockReason}).`;
          inputBlockedReplace.set(sid, refusal);
          await post(`/sessions/${sid}/guard/output`, {
            content: refusal,
            trace_id: traceId || undefined,
            trust: true,
            metadata: { source: "openclaw-plugin", hook: "llm_output", environment },
          }).catch(() => {});
          return;
        }

        const result = await post(`/sessions/${sid}/guard/output`, {
          content,
          trace_id: traceId || undefined,
          metadata: { source: "openclaw-plugin", hook: "llm_output", environment },
        });

        guardedOutputTurns.add(sid);

        if (result?.blocked) {
          const reason = String(result?.block_reason || "safety policy violation");
          const replacement = `I'm not able to share that response. Reason: ${reason}.`;
          assistantTexts.splice(0, assistantTexts.length, replacement);
          api.logger.warn(`[aegis-guard] output blocked sid=${sid} score=${result?.output_score ?? "?"} reason=${reason}`);
        }
      } catch (err) {
        api.logger.warn(`[aegis-guard] llm_output: ${String(err)}`);
      }
    });

    /** Final outbound gate — last chance to cancel before the message is delivered */
    api.on("message_sending", async (event: any, ctx: any) => {
      if (!enforceOutputGate) return undefined;
      try {
        const content = String(event?.content || "");
        if (!content.trim()) return undefined;

        // Only gate output within an existing session — startup greetings and other
        // internal messages that have no corresponding user prompt should be skipped.
        const sid = findSession(event, ctx, msgKey(ctx));
        if (!sid) return undefined;
        bind(sid, event, ctx);

        // Input-blocked turns: force the hardcoded refusal regardless of LLM output.
        // guard/output was already recorded as trusted in llm_output.
        if (inputBlockedReplace.has(sid)) {
          const refusal = inputBlockedReplace.get(sid)!;
          inputBlockedReplace.delete(sid);
          guardedOutputTurns.delete(sid);
          return { content: refusal };
        }

        // llm_output already guarded this turn — skip to avoid duplicate trace
        if (guardedOutputTurns.has(sid)) {
          guardedOutputTurns.delete(sid);
          return undefined;
        }

        const traceId = pendingTraceIds.get(sid);
        if (traceId) pendingTraceIds.delete(sid);

        const result = await post(`/sessions/${sid}/guard/output`, {
          content,
          trace_id: traceId || undefined,
          metadata: { source: "openclaw-plugin", hook: "message_sending", environment },
        });

        if (result?.blocked) {
          const reason = String(result?.block_reason || "safety policy violation");
          api.logger.warn(`[aegis-guard] outbound blocked sid=${sid} score=${result?.output_score ?? "?"} reason=${reason}`);
          return { content: `I'm not able to share that response. Reason: ${reason}.` };
        }
      } catch (err) {
        api.logger.warn(`[aegis-guard] message_sending: ${String(err)}`);
      }
      return undefined;
    });
  },
};

export default plugin;
