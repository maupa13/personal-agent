# Gap Analysis — v0.2.5 vs MASTER-SPEC 1.0

Canonical source: `docs/specification/MASTER-SPEC.md`.

## Implemented baseline
Browser-first Docker shell; local Ollama; Provider/Model Registry foundation; external OpenAI-compatible provider discovery; ADMIN routing; registration/login/session foundation; structured presets; CSP/security boundary; Windows lifecycle/release-gate framework.

## Major gaps
1. Web/Search/URL/Research absent; URL requests are only blocked from hallucinating.
2. Conversation/context/memory are not yet server-side production architecture.
3. Files/Workspace/Artifact Manager absent.
4. Code sandbox/agent absent.
5. Image/audio/video workers absent.
6. Connectors/MCP/skills/automation absent.
7. Full multi-tenant PostgreSQL/Redis/object storage, billing/quota and operations remain future production slices.

## Current decision
Implement Web/Search/URL/Research as the next vertical slice. It closes an existing correctness gap and establishes evidence/tool contracts reused by Files, Code and Connectors.
