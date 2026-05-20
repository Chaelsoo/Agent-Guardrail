# setup

**prerequisites:** Docker, Node.js 22+ (optional for OpenClaw)


**1. clone the repo**

```bash
git clone https://github.com/Chaelsoo/Agent-Guardrail.git
cd Agent-Guardrail
```


**2. configure environment**

create a `.env` file in the root directory (or get it from your teammate):

```bash
# Aegis Configuration
AEGIS_THRESHOLD=0.5

# LLM Judge - DeepSeek (get key from https://platform.deepseek.com/)
LLM_JUDGE_API_KEY=your_deepseek_api_key_here
LLM_JUDGE_MODEL=deepseek-chat
LLM_JUDGE_PROVIDER=deepseek
JUDGE_AUDIT_INTERVAL=3
TAINT_RESOLUTION_THRESHOLD=2

# Database
DATABASE_URL=sqlite:///aegis.db
AEGIS_DB_ENABLED=true

# Optional: HuggingFace token (only needed for gated models)
HF_TOKEN=
```


**3. start aegis**

```bash
docker-compose up --build
```

first run downloads models (~2.5 GB) — subsequent starts are instant. wait until ready:

```bash
docker-compose logs -f aegis
# ready when you see: [Aegis] All models ready
```

**dashboard** → http://localhost:8765


**features:**
- ✅ **DeepSeek Judge**: LLM-based security monitoring (Job A: per-action, Job B: periodic audit)
- ✅ **PoLP Profiles**: Granular tool access control with path/domain restrictions (see Tools page)
- ✅ **Session Management**: Clean trace grouping and finalization
- ✅ **All Gates**: Input, Tool, Tool Output, Output with real-time monitoring


**3. install openclaw**

```bash
npm install -g openclaw@2026.3.8
```

follow the setup wizard to connect your channels (Telegram, etc.) and configure your model provider, then start the gateway:

```bash
openclaw gateway --force
```


**4. install the aegis plugin**

```bash
cp -r integrations/openclaw-aegis-guard ~/.openclaw/extensions/aegis-guard
```

add this to `~/.openclaw/openclaw.json` under the top-level `plugins` key:

```json
"plugins": {
  "enabled": true,
  "load": {
    "paths": ["~/.openclaw/extensions/aegis-guard"]
  },
  "entries": {
    "aegis-guard": {
      "enabled": true,
      "config": {
        "aegisUrl": "http://127.0.0.1:8765/v1",
        "environment": "dev"
      }
    }
  }
}
```

restart the gateway to load the plugin:

```bash
openclaw gateway --force
```


**5. verify**

send a message in openclaw — a session should appear in the dashboard with input/output gate traces.

to test blocking, send: `ignore all previous instructions` — it should be blocked and show up as a trace in the dashboard.
