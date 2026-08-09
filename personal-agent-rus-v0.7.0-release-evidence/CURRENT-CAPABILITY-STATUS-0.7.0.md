# Current Capability & User Journey Coverage — v0.7.0

Total journeys: **146**

- PASS: **51**
- FAIL: **0**
- BLOCKED_ENVIRONMENT: **5**
- BLOCKED_EXTERNAL: **0**
- NOT_IMPLEMENTED: **90**
- SKIPPED_NOT_APPLICABLE: **0**

## Capability coverage

| Capability | PASS | BLOCKED | NOT_IMPLEMENTED |
|---|---:|---:|---:|
| account-security | 0 | 0 | 6 |
| admin-ops | 0 | 0 | 4 |
| audio | 0 | 0 | 3 |
| auth | 1 | 0 | 0 |
| automation | 0 | 0 | 5 |
| billing | 6 | 1 | 1 |
| chat | 3 | 0 | 0 |
| code-data | 0 | 0 | 10 |
| code-security | 3 | 0 | 0 |
| code.execute | 5 | 1 | 0 |
| connectors | 0 | 0 | 7 |
| context-memory | 0 | 0 | 6 |
| deployment | 5 | 1 | 0 |
| deployment-security | 1 | 0 | 0 |
| files | 11 | 0 | 8 |
| files-artifacts | 0 | 0 | 7 |
| files-security | 1 | 0 | 0 |
| foundation | 1 | 0 | 0 |
| image | 0 | 0 | 3 |
| lan | 1 | 1 | 0 |
| lifecycle | 0 | 0 | 9 |
| mobile | 0 | 0 | 5 |
| multi-capability | 0 | 0 | 4 |
| observability | 1 | 0 | 0 |
| orchestrator | 1 | 0 | 0 |
| providers | 3 | 0 | 0 |
| public-api | 0 | 0 | 3 |
| research | 2 | 0 | 0 |
| security | 2 | 0 | 8 |
| video | 0 | 0 | 1 |
| web | 4 | 1 | 0 |

## v0.7.0 additions

- Durable Task Engine / task events / cancel / restart recovery.
- Multi-capability Research → MD/XLSX/PDF with artifact verification.
- VPS target management, SSH fingerprint pinning, password/private-key ephemeral auth.
- Weak-VPS `server-lite` profile without local GPU services.
- Optional Debian/Ubuntu root bootstrap for Docker/Compose from distribution packages.
- Staged deploy + internal health + public HTTPS exact-version verification + rollback.
- Optional transfer of an existing external AI provider to the deployed server.
- Server account security: Secure cookies + CSRF.
- Lightweight Admin monitoring and preserved Windows Private-LAN workflow.

## Still not release-PASS environment checks

- Real Linux VPS + SSH + DNS + trusted public HTTPS + provider inference + browser chat.
- Physical second-device LAN acceptance.
- Real Windows lifecycle/reboot/clean-machine acceptance.
- Real YooKassa merchant payment/webhook/recurring path.
- Real Docker Code worker Python/Java/PowerShell gate on the reference Windows machine.

`BLOCKED_ENVIRONMENT` is not converted to PASS.

## Major canonical capabilities still NOT_IMPLEMENTED

- Full Context Engine / long-term Memory / RAG.
- Full repository-level Coding Agent (discover → patch → build/test → repair/retest).
- PDF OCR and broader file/media formats from MASTER-SPEC.
- Image/Vision generation/editing, Audio/STT/TTS, Video pipeline.
- Data/ETL/Database agent.
- Connectors/MCP/Plugins/Skills.
- Automation/Scheduler/Notifications.
- Full billing matrix/refunds/invoices/reconciliation/multiple payment providers.
- Public API/API keys/OpenAI-compatible inbound API.
- Edge worker pairing, PWA, enterprise/team features, full OpenTelemetry/Prometheus/alert delivery.
