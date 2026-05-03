# setup

**prerequisites:** Docker, Node.js 22+, a HuggingFace account with access to [qualifire/prompt-injection-sentinel](https://huggingface.co/qualifire/prompt-injection-sentinel)

---

**1. clone the repo**

```bash
git clone https://github.com/Chaelsoo/Agent-Guardrail.git
cd Agent-Guardrail
```

---

**2. start aegis**

add your HuggingFace token to `docker-compose.yml`:

```yaml
environment:
  - HF_TOKEN=hf_your_token_here
```

then:

```bash
docker compose up -d --build
```

first run downloads ~2.5 GB of models into a persistent volume — subsequent starts are instant. wait until ready:

```bash
docker compose logs -f aegis
# ready when you see: [Aegis] All models ready
```

dashboard → http://localhost:8765

---

**3. install openclaw**

```bash
npm install -g openclaw@2026.3.8
```

follow the setup wizard to connect your channels (Telegram, etc.) and configure your model provider, then start the gateway:

```bash
openclaw gateway --force
```

---

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

---

**5. verify**

send a message in openclaw — a session should appear in the dashboard with input/output gate traces.

to test blocking, send: `ignore all previous instructions` — it should be blocked and show up as a trace in the dashboard.
