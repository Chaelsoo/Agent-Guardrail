# Aegis — Setup Guide

Three things to run: the **backend** (Aegis), the **frontend** (dashboard), and optionally the **OpenClaw plugin**.

---

## 1. Backend (Aegis)

### Install

```bash
git clone https://github.com/Chaelsoo/Agent-Guardrail.git
cd Agent-Guardrail

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
# Edit .env if needed — defaults work out of the box
```

### Start

```bash
.venv/bin/python -m uvicorn backend.api.app:app --host 0.0.0.0 --port 8765
```

On first start, three models are downloaded and cached (~1.5 GB):

```
[Aegis] Loading classifier (qualifire/prompt-injection-sentinel)...
[Aegis] Loading embedder (all-MiniLM-L6-v2)...
[Aegis] Loading tool call verifier (llm-semantic-router/toolcall-verifier)...
[Aegis] All models ready
[Aegis] ready: http://127.0.0.1:8765/
```

Verify it's running:

```bash
curl http://localhost:8765/v1/aegis/health
```

---

## 2. Frontend (Dashboard)

The dashboard is pre-built — it's served automatically by the backend at `http://localhost:8765/`.  
Open that URL in your browser. No extra step needed.

### Rebuild after frontend changes

Only needed if you modify files under `frontend/src/`:

```bash
cd frontend
npm install        # or: pnpm install
npm run build      # outputs to frontend/dist/
```

Then restart the backend — it picks up the new build automatically.

---

## 3. OpenClaw Plugin

Requires [OpenClaw](https://openclaw.ai) installed (`npm install -g openclaw`).

### Install the plugin

From the project root:

```bash
openclaw plugins install path ./integrations/openclaw-aegis-guard
```

### Configure

Add the following to your `~/.openclaw/openclaw.json` under `plugins`:

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

### Start the gateway

```bash
openclaw gateway --force
```

You should see:

```
[plugins] aegis-guard: loaded ...
```

### Verify

Send any message in OpenClaw, then check the dashboard at `http://localhost:8765/` — a new session should appear with input/output gate traces.

---

## Startup order

1. Start Aegis backend first (port 8765 must be up before OpenClaw connects)
2. Start OpenClaw gateway
3. Open dashboard in browser

---

## Ports

| Service | Port |
|---------|------|
| Aegis API + Dashboard | 8765 |
| OpenClaw gateway | 18789 (default) |
