# Personal Agent Rus v0.3 — Ordered Implementation Backlog

## P0 — Identity / Provider foundation

1. Migrate routing DB from `model_id` to `(provider_id, model_id)`.
2. Add providers table and local system-managed Ollama provider.
3. Add provider adapters for Ollama and OpenAI-compatible APIs.
4. Add automatic discovery and unified inventory API.
5. Replace manual model-ID-first Admin UI with provider/inventory UI.
6. Retain managed model pull for Ollama.
7. Add provider health/test actions and secret redaction.
8. Add structured presets: explain/write/analyze.
9. Add auth-mode/register/login/session foundation.
10. Add machine-readable acceptance entries.

## P1 — Chat server persistence / identity boundary

1. Server-side conversations and messages.
2. Ownership by user/session.
3. Migrate anonymous/local history where possible.
4. USER account menu / login/register surfaces.
5. Admin users surface.

## P2 — Web

1. Search adapter.
2. Safe URL fetcher + SSRF policy.
3. Dynamic browser worker.
4. Evidence/source records.
5. Research synthesis.
6. DTF/Habr/etc. deterministic + live journeys.

## P3 — Files

1. Per-user workspace.
2. Upload/download contract.
3. TXT/MD/JSON/CSV.
4. PDF/DOCX/XLSX/PPTX adapters.
5. Artifact validation and versioning.

## P4 — Code

1. Separate execution worker.
2. Python.
3. PowerShell.
4. Java.
5. Resource isolation/cancellation.
6. compile/test/repair E2E.

## Rule

A UI capability is marked `ready` only when its required vertical slice and USER journey pass. Until then it remains visibly unavailable and cannot silently fall through to plain LLM chat.
