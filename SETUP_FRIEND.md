# Aegis Setup Guide

## Quick Start

1. **Clone the repo and checkout the branch**
   ```bash
   git clone <repo-url>
   cd agent-guardrail
   git checkout <branch-name>
   ```

2. **Add the .env file**
   - Get the `.env` file from your friend
   - Place it in the root directory: `agent-guardrail/.env`

3. **Start Aegis**
   ```bash
   docker-compose up --build
   ```
   
   Wait for: `[Aegis] All models ready`

4. **Open dashboard**
   - Go to: http://localhost:8765
   - You should see the Aegis dashboard

## Testing

Run a test:
```bash
curl -X POST http://localhost:8765/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "test"}'
```

## What's Configured

- **DeepSeek Judge**: LLM-based security monitoring
- **PoLP Profiles**: Tool access control (see Tools page in dashboard)
- **Session Management**: Trace grouping and finalization
- **All Gates**: Input, Tool, Tool Output, Output

## Dashboard Features

- **Sessions**: View active agent sessions
- **Traces**: See complete conversation flows with all gates
- **Tools**: Configure PoLP rules (path/domain restrictions)
- **Network**: Manage allowlist/denylist

## Troubleshooting

**Container won't start:**
```bash
docker-compose logs aegis
```

**Port already in use:**
```bash
docker-compose down
# Change port in docker-compose.yml if needed
docker-compose up
```

**Models not loading:**
- Check Docker has enough memory (8GB+ recommended)
- Wait 2-3 minutes for HuggingFace models to download

## API Endpoints

All endpoints: `http://localhost:8765/v1/`

- `POST /sessions` - Create session
- `POST /sessions/{id}/guard/input` - Input gate
- `POST /sessions/{id}/guard/tool` - Tool gate
- `POST /sessions/{id}/guard/tool_output` - Tool output gate
- `POST /sessions/{id}/guard/output` - Output gate
- `GET /polp/profile` - View PoLP rules
- `GET /sessions/{id}` - Get session traces

Enjoy! 🚀
