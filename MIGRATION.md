# Personal Agent Rus -> shared local-ai migration

Current Docker Desktop shows duplicate infrastructure:
- `par-rus-ollama` and `ai-ollama`;
- `par-rus-searxng` and `ai-searxng`;
- plus a standalone `ollama`.

Target:
```text
local-ai-network
├─ ai-ollama
├─ ai-searxng
├─ ai-whisper
├─ ai-speaches
├─ ai-comfyui
├─ ai-playwright
├─ ai-open-webui
└─ Personal Agent containers
   ├─ par-rus-core
   ├─ par-rus-code-worker
   └─ par-rus-browser
```

## Safe migration order

1. Back up Personal Agent data/config.
2. Start the canonical `local-ai`.
3. Run `CONNECT-EXISTING-TO-SHARED-NETWORK.ps1`.
4. Verify from Personal Agent containers that Docker DNS resolves `ollama` and `searxng`.
5. Update the actual Personal Agent compose/env to use shared endpoints:
   - Ollama: `http://ollama:11434`
   - SearXNG: `http://searxng:8080`
6. Recreate only Personal Agent application containers.
7. Only after successful smoke tests, stop/remove `par-rus-ollama` and `par-rus-searxng`.
8. Do NOT remove their volumes until you are sure they contain no unique models/data.

The exact Personal Agent environment variable names must be taken from the current rc.16 source/compose.
This pack intentionally does not invent them.
