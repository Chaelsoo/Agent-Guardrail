import { useState, useEffect, useRef } from 'react';
import { SessionList } from '../components/session-list';
import { TraceTimeline } from '../components/trace-timeline';
import { AgentIcon } from '../components/agent-icon';
import { SeverityBadge } from '../components/severity-badge';
import { Session, Trace, TraceStatus, AgentType, PipelineStep, SeverityLevel } from '../types';
import { Activity } from 'lucide-react';

const BASE = 'http://localhost:8765/v1';

const AGENT_TYPE_MAP: Record<string, AgentType> = {
  pentest: 'research',
  code_execution: 'code-generation',
  customer_support: 'customer-support',
  data_retrieval: 'data-analysis',
  general: 'research',
};

const VERDICT_MAP: Record<string, TraceStatus> = {
  allowed: 'allowed',
  blocked: 'blocked',
  redacted: 'redacted',
  warned: 'flagged',
  flagged: 'flagged',
};

const SPAN_STATUS_MAP: Record<string, TraceStatus> = {
  pass: 'allowed',
  block: 'blocked',
  redact: 'redacted',
  warn: 'flagged',
  skipped: 'allowed',
  approval_required: 'flagged',
};

function mapSession(s: any): Session {
  const agentType = AGENT_TYPE_MAP[s.agent_type] ?? 'research';
  const ts = new Date(s.created_at * 1000);
  return {
    id: s.session_id,
    agentType,
    severity: (s.severity?.toLowerCase() ?? 'low') as SeverityLevel,
    riskScore: Math.round((s.cumulative_risk ?? 0) * 100),
    startTime: ts,
    lastActivity: ts,
    traceCount: s.trace_count ?? 0,
  };
}

function mapSpan(span: any, idx: number): PipelineStep {
  return {
    id: `${span.name}-${idx}`,
    name: span.tool_name ? `${span.name}:${span.tool_name}` : (span.name ?? 'unknown'),
    status: SPAN_STATUS_MAP[span.status] ?? 'allowed',
    duration: span.duration_ms ?? 0,
    detail: span.detail ?? undefined,
    detections: span.rules?.length ? span.rules : undefined,
    isTool: !!(span.tool_name || span.name === 'tool_pre' || span.name === 'tool_post' ||
               /^Tool\s*[·\-]/i.test(span.name ?? '')),
  };
}

function mapTrace(t: any): Trace {
  const steps: PipelineStep[] = (t.spans ?? []).map(mapSpan);
  const rawContent: string = t.prompt ?? '';
  // Strip internal prefixes from display content
  const content = rawContent.replace(/^\[tool(?:-result)?:[^\]]*\]\s*/, '') || 'Tool execution';
  return {
    id: t.trace_id,
    sessionId: t.session_id,
    timestamp: new Date(t.ts * 1000),
    direction: 'prompt',
    content,
    status: VERDICT_MAP[t.verdict] ?? 'allowed',
    steps,
    totalDuration: t.duration_ms ?? 0,
    llmOutput: t.llm_output ?? undefined,
    finalized: t.finalized !== false,
  };
}

const agentTypeLabels: Record<string, string> = {
  'customer-support': 'Customer Support',
  'data-analysis': 'Data Analysis',
  'code-generation': 'Code Generation',
  'research': 'Research',
};

export function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [traces, setTraces] = useState<Trace[]>([]);
  const esRef = useRef<EventSource | null>(null);

  // Fetch + poll sessions
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await fetch(`${BASE}/sessions`);
        const data: any[] = await res.json();
        // Filter out ended sessions
        const active = data.filter(s => !s.ended);
        const mapped = active.map(mapSession);
        setSessions(mapped);
        // Auto-select first session if none selected
        setSelectedSessionId(prev => prev ?? (mapped[0]?.id || null));
      } catch { /* ignore */ }
    };
    fetchSessions();
    const interval = setInterval(fetchSessions, 5000);
    return () => clearInterval(interval);
  }, []);

  // When session changes: load existing traces then connect SSE
  useEffect(() => {
    if (!selectedSessionId) return;

    // Close previous SSE
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
    setTraces([]);

    // Load existing traces first
    fetch(`${BASE}/sessions/${selectedSessionId}`)
      .then(r => r.json())
      .then(data => {
        const existing: Trace[] = (data.traces ?? []).map(mapTrace).reverse();
        setTraces(existing);
      })
      .catch(() => {});

    // Connect SSE
    const es = new EventSource(`${BASE}/sessions/${selectedSessionId}/events/stream`);
    esRef.current = es;

    es.onmessage = (ev) => {
      if (!ev.data?.trim()) return;
      try {
        const t = mapTrace(JSON.parse(ev.data));
        setTraces(prev => {
          const idx = prev.findIndex(x => x.id === t.id);
          if (idx !== -1) {
            const next = [...prev];
            next[idx] = t;
            return next;
          }
          return [t, ...prev];
        });
      } catch { /* ignore */ }
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [selectedSessionId]);

  const selectedSession = sessions.find(s => s.id === selectedSessionId);

  return (
    <div className="flex h-screen">
      {/* Session list sidebar */}
      <div className="w-80 border-r border-[#1e293b] bg-[#0f1419]">
        <SessionList
          sessions={sessions}
          selectedSessionId={selectedSessionId}
          onSelectSession={setSelectedSessionId}
        />
      </div>

      {/* Main content area */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {selectedSession ? (
          <>
            {/* Session header */}
            <div className="border-b border-[#1e293b] bg-[#0f1419] px-6 py-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <AgentIcon type={selectedSession.agentType} className="w-5 h-5 text-[#3b82f6]" />
                  <div>
                    <h1 className="text-[15px] text-[#e4e7eb]">
                      {agentTypeLabels[selectedSession.agentType]}
                    </h1>
                    <p className="text-[11px] text-[#94a3b8]">
                      {selectedSession.id}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <SeverityBadge severity={selectedSession.severity} size="md" />
                  <div className="flex items-center gap-2 text-[11px]">
                    <div className="w-2 h-2 bg-[#10b981] rounded-full animate-pulse" />
                    <span className="text-[#94a3b8]">Live</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-6 text-[11px] text-[#94a3b8]">
                <span>Risk Score: <span className="text-[#e4e7eb]">{selectedSession.riskScore}</span></span>
                <span>•</span>
                <span>{traces.length} traces</span>
              </div>
            </div>

            {/* Trace timeline */}
            <div className="flex-1 overflow-y-auto p-6">
              {traces.length > 0 ? (
                <TraceTimeline traces={traces} />
              ) : (
                <div className="flex items-center justify-center h-full text-[#64748b] text-[13px]">
                  Waiting for traces…
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-[#64748b]">
            <div className="text-center">
              <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-[13px]">Select a session to view traces</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
