# Current Capability & User Journey Coverage — v0.5.0

Canonical source: `docs/specification/MASTER-SPEC.md`.

This document is a status view, not a replacement for the canonical specification.

## account-security

Status summary: `NOT_IMPLEMENTED` 6

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-600 | **NOT_IMPLEMENTED** | Email verification according to policy | — |
| UJ-601 | **NOT_IMPLEMENTED** | Password reset single-use expiry | — |
| UJ-602 | **NOT_IMPLEMENTED** | Session list and revoke | — |
| UJ-603 | **NOT_IMPLEMENTED** | 2FA/TOTP and backup codes | — |
| UJ-604 | **NOT_IMPLEMENTED** | Personal cabinet profile/privacy/memory/storage | — |
| UJ-605 | **NOT_IMPLEMENTED** | Data export and delete account | — |

## admin-ops

Status summary: `NOT_IMPLEMENTED` 4

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-660 | **NOT_IMPLEMENTED** | Admin user suspend/unsuspend/plan/quota | — |
| UJ-661 | **NOT_IMPLEMENTED** | Admin provider health/priority/pricing/privacy | — |
| UJ-662 | **NOT_IMPLEMENTED** | Admin queues/workers/storage/health | — |
| UJ-663 | **NOT_IMPLEMENTED** | Audit log sensitive admin actions | — |

## audio

Status summary: `NOT_IMPLEMENTED` 3

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-420 | **NOT_IMPLEMENTED** | Audio transcription with timestamps | — |
| UJ-421 | **NOT_IMPLEMENTED** | Diarization/summary/action items | — |
| UJ-422 | **NOT_IMPLEMENTED** | TTS playable output | — |

## auth

Status summary: `PASS` 1

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-020 | **PASS** | Registration/login/session | AUTH-001, AUTH-002 |

## automation

Status summary: `NOT_IMPLEMENTED` 5

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-540 | **NOT_IMPLEMENTED** | One-time scheduled task | — |
| UJ-541 | **NOT_IMPLEMENTED** | Recurring timezone-aware task | — |
| UJ-542 | **NOT_IMPLEMENTED** | Condition-based monitor | — |
| UJ-543 | **NOT_IMPLEMENTED** | Restart recovers schedules without duplicates | — |
| UJ-544 | **NOT_IMPLEMENTED** | Automation notification delivery | — |

## billing

Status summary: `NOT_IMPLEMENTED` 6

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-620 | **NOT_IMPLEMENTED** | Plan entitlement enforcement | — |
| UJ-621 | **NOT_IMPLEMENTED** | Usage metering per model/provider | — |
| UJ-622 | **NOT_IMPLEMENTED** | Payment success + idempotent webhook | — |
| UJ-623 | **NOT_IMPLEMENTED** | Upgrade/downgrade/grace/cancel | — |
| UJ-624 | **NOT_IMPLEMENTED** | BYOK usage separated from platform cost | — |
| UJ-625 | **NOT_IMPLEMENTED** | Quota exhaustion local/private fallback | — |

## chat

Status summary: `PASS` 3

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-010 | **PASS** | First chat with real inference | FND-API-001 |
| UJ-011 | **PASS** | Refresh and continue conversation | FND-BROWSER-OFFLINE-001 |
| UJ-014 | **PASS** | Switch Auto/Fast/Smart modes | FND-BROWSER-OFFLINE-001 |

## code-data

Status summary: `NOT_IMPLEMENTED` 10

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-300 | **NOT_IMPLEMENTED** | Python generate/execute/test | — |
| UJ-301 | **NOT_IMPLEMENTED** | PowerShell generate/execute/test | — |
| UJ-302 | **NOT_IMPLEMENTED** | Java project discover/modify/compile/JUnit/retest | — |
| UJ-303 | **NOT_IMPLEMENTED** | Failing tests diagnose/fix/regression | — |
| UJ-304 | **NOT_IMPLEMENTED** | Code timeout and cancellation | — |
| UJ-305 | **NOT_IMPLEMENTED** | Sandbox filesystem escape blocked | — |
| UJ-306 | **NOT_IMPLEMENTED** | Sandbox Docker socket/secrets blocked | — |
| UJ-320 | **NOT_IMPLEMENTED** | CSV/XLSX data clean/transform/visualize | — |
| UJ-321 | **NOT_IMPLEMENTED** | SQL schema/query/optimization | — |
| UJ-322 | **NOT_IMPLEMENTED** | ETL API + file + database | — |

## code-security

Status summary: `PASS` 3

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-295 | **PASS** | Execution output is bounded and runtime secrets are not inherited by user code | CODE-009, CODE-010 |
| UJ-296 | **PASS** | Sandbox has no network/Docker socket and uses read-only bounded runtime | CODE-011 |
| UJ-297 | **PASS** | Code job ownership is isolated between accounts | CODE-006 |

## code.execute

Status summary: `BLOCKED_ENVIRONMENT` 1, `PASS` 5

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-290 | **PASS** | Run Python snippet in isolated sandbox and inspect stdout/stderr/exit code | CODE-001, CODE-012 |
| UJ-291 | **PASS** | Compile and run Java 21 snippet in isolated sandbox | CODE-002 |
| UJ-292 | **PASS** | Run PowerShell snippet through sandbox command contract | CODE-003 |
| UJ-293 | **PASS** | Compilation/non-zero process failure is surfaced, never reported as success | CODE-004, CODE-005 |
| UJ-294 | **PASS** | Timeout and cancellation terminate sandbox process tree | CODE-007, CODE-008 |
| UJ-298 | **BLOCKED_ENVIRONMENT** | Reference Windows Docker image executes real Python, Java and PowerShell | CODE-LIVE-001 |

## connectors

Status summary: `NOT_IMPLEMENTED` 7

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-500 | **NOT_IMPLEMENTED** | REST connector read | — |
| UJ-501 | **NOT_IMPLEMENTED** | OAuth connect/refresh/revoke | — |
| UJ-502 | **NOT_IMPLEMENTED** | Read-only connector cannot write | — |
| UJ-503 | **NOT_IMPLEMENTED** | External write requires permission | — |
| UJ-504 | **NOT_IMPLEMENTED** | Connector outage gives PARTIAL/BLOCKED | — |
| UJ-520 | **NOT_IMPLEMENTED** | MCP server capability discovery | — |
| UJ-521 | **NOT_IMPLEMENTED** | Plugin manifest permissions | — |

## context-memory

Status summary: `NOT_IMPLEMENTED` 6

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-150 | **NOT_IMPLEMENTED** | 50+ message coherent conversation | — |
| UJ-151 | **NOT_IMPLEMENTED** | Context compression respects model window | — |
| UJ-152 | **NOT_IMPLEMENTED** | Restart restores conversation semantics | — |
| UJ-153 | **NOT_IMPLEMENTED** | User views/edits/deletes memory | — |
| UJ-154 | **NOT_IMPLEMENTED** | Large document selective retrieval | — |
| UJ-155 | **NOT_IMPLEMENTED** | Model context switch without overflow | — |

## files

Status summary: `NOT_IMPLEMENTED` 8, `PASS` 11

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-200 | **PASS** | Upload/read/analyze TXT | FILE-001, FILE-012, FILE-017 |
| UJ-201 | **PASS** | Upload/read/analyze MD | FILE-002, FILE-012, FILE-017 |
| UJ-202 | **PASS** | Upload/read/analyze JSON | FILE-003, FILE-012, FILE-017 |
| UJ-203 | **PASS** | Upload/read/analyze CSV | FILE-004, FILE-012, FILE-017 |
| UJ-204 | **PASS** | Upload/read/analyze PDF text | FILE-005, FILE-012, FILE-017 |
| UJ-205 | **NOT_IMPLEMENTED** | Upload/read/analyze PDF scan/OCR | — |
| UJ-206 | **PASS** | Upload/read/analyze DOCX | FILE-006, FILE-012, FILE-017 |
| UJ-207 | **PASS** | Upload/read/analyze XLSX | FILE-007, FILE-012, FILE-017 |
| UJ-208 | **PASS** | Upload/read/analyze PPTX | FILE-008, FILE-012, FILE-017 |
| UJ-209 | **NOT_IMPLEMENTED** | Upload/read/analyze ZIP | — |
| UJ-210 | **NOT_IMPLEMENTED** | Upload/read/analyze image | — |
| UJ-211 | **NOT_IMPLEMENTED** | Upload/read/analyze audio | — |
| UJ-212 | **NOT_IMPLEMENTED** | Upload/read/analyze video | — |
| UJ-213 | **NOT_IMPLEMENTED** | Upload/read/analyze Java | — |
| UJ-214 | **NOT_IMPLEMENTED** | Upload/read/analyze Python | — |
| UJ-215 | **NOT_IMPLEMENTED** | Upload/read/analyze PowerShell | — |
| UJ-216 | **PASS** | Create verified artifact in supported format and download it | FILE-001, FILE-002, FILE-003, FILE-004, FILE-005, FILE-006, FILE-007, FILE-008 |
| UJ-217 | **PASS** | Modify artifact as a verified new version | FILE-011 |
| UJ-218 | **PASS** | Workspace/artifact isolation between accounts | FILE-014 |

## files-artifacts

Status summary: `NOT_IMPLEMENTED` 7

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-220 | **NOT_IMPLEMENTED** | Create validated artifact | — |
| UJ-221 | **NOT_IMPLEMENTED** | Edit existing artifact and preserve unrelated content | — |
| UJ-222 | **NOT_IMPLEMENTED** | Download artifact with authorization | — |
| UJ-223 | **NOT_IMPLEMENTED** | Malformed file controlled failure | — |
| UJ-224 | **NOT_IMPLEMENTED** | Large file resource policy | — |
| UJ-225 | **NOT_IMPLEMENTED** | Archive zip-slip/bomb protection | — |
| UJ-226 | **NOT_IMPLEMENTED** | Multi-artifact XLSX + PDF report | — |

## files-security

Status summary: `PASS` 1

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-219 | **PASS** | Reject malformed, oversized and path-traversal file inputs | FILE-009, FILE-010, FILE-015, FILE-016 |

## foundation

Status summary: `PASS` 1

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-001 | **PASS** | Fresh package start | FND-START-001 |

## image

Status summary: `NOT_IMPLEMENTED` 3

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-400 | **NOT_IMPLEMENTED** | Image upload and vision analysis | — |
| UJ-401 | **NOT_IMPLEMENTED** | Image generation artifact | — |
| UJ-402 | **NOT_IMPLEMENTED** | Image edit/inpainting/upscale | — |

## lifecycle

Status summary: `NOT_IMPLEMENTED` 9

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-700 | **NOT_IMPLEMENTED** | STOP -> START preserves state | — |
| UJ-701 | **NOT_IMPLEMENTED** | RESTART preserves state | — |
| UJ-702 | **NOT_IMPLEMENTED** | REPAIR healthy is idempotent | — |
| UJ-703 | **NOT_IMPLEMENTED** | REPAIR damaged runtime preserves data | — |
| UJ-704 | **NOT_IMPLEMENTED** | Backup -> restore verified | — |
| UJ-705 | **NOT_IMPLEMENTED** | Update -> migrate -> verify | — |
| UJ-706 | **NOT_IMPLEMENTED** | Failed update rollback including data | — |
| UJ-707 | **NOT_IMPLEMENTED** | Real Windows reboot recovery | — |
| UJ-708 | **NOT_IMPLEMENTED** | Clean machine bootstrap | — |

## mobile

Status summary: `NOT_IMPLEMENTED` 5

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-760 | **NOT_IMPLEMENTED** | Mobile registration/login/chat | — |
| UJ-761 | **NOT_IMPLEMENTED** | Mobile file/image/audio upload | — |
| UJ-762 | **NOT_IMPLEMENTED** | Mobile artifact download | — |
| UJ-763 | **NOT_IMPLEMENTED** | Real mobile microphone secure-context journey | — |
| UJ-764 | **NOT_IMPLEMENTED** | PWA install/share/push readiness | — |

## multi-capability

Status summary: `NOT_IMPLEMENTED` 4

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-800 | **NOT_IMPLEMENTED** | Research -> XLSX -> PDF with verified sources/artifacts | — |
| UJ-801 | **NOT_IMPLEMENTED** | Uploaded document -> research -> revised document | — |
| UJ-802 | **NOT_IMPLEMENTED** | Web -> code -> validated artifact | — |
| UJ-803 | **NOT_IMPLEMENTED** | External API read -> compare file -> permission -> external write | — |

## providers

Status summary: `PASS` 3

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-021 | **PASS** | Discover local provider models | PRV-001, PRV-002 |
| UJ-022 | **PASS** | Connect OpenAI-compatible provider and discover models | PRV-004, PRV-005 |
| UJ-023 | **PASS** | Assign provider+model routing and persist | PRV-006 |

## public-api

Status summary: `NOT_IMPLEMENTED` 3

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-640 | **NOT_IMPLEMENTED** | User API key create/use/revoke | — |
| UJ-641 | **NOT_IMPLEMENTED** | Inbound OpenAI-compatible chat | — |
| UJ-642 | **NOT_IMPLEMENTED** | Rate limit by user/tenant/key | — |

## research

Status summary: `PASS` 2

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-103 | **PASS** | Ask for current news and automatically invoke Web | WEB-005 |
| UJ-104 | **PASS** | Multi-source research with sources | WEB-006 |

## security

Status summary: `NOT_IMPLEMENTED` 8, `PASS` 2

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-106 | **PASS** | Web SSRF/private redirect attack is blocked | WEB-008, WEB-009 |
| UJ-107 | **PASS** | Malicious Web prompt injection remains untrusted data | WEB-010 |
| UJ-730 | **NOT_IMPLEMENTED** | Tenant IDOR blocked | — |
| UJ-731 | **NOT_IMPLEMENTED** | CSRF blocked | — |
| UJ-732 | **NOT_IMPLEMENTED** | XSS blocked | — |
| UJ-733 | **NOT_IMPLEMENTED** | SQL injection blocked | — |
| UJ-734 | **NOT_IMPLEMENTED** | Prompt injection blocked | — |
| UJ-735 | **NOT_IMPLEMENTED** | Secret leakage attempt blocked | — |
| UJ-736 | **NOT_IMPLEMENTED** | Upload abuse blocked | — |
| UJ-737 | **NOT_IMPLEMENTED** | Rate-limit abuse handled | — |

## video

Status summary: `NOT_IMPLEMENTED` 1

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-440 | **NOT_IMPLEMENTED** | Video transcript/scenes/keyframes/OCR/summary | — |

## web

Status summary: `BLOCKED_ENVIRONMENT` 1, `PASS` 4

| Journey | Status | Scenario | Evidence |
|---|---|---|---|
| UJ-100 | **PASS** | Search Web and show normalized results | WEB-001 |
| UJ-101 | **PASS** | Read a specific URL through static/browser pipeline | WEB-002, WEB-003 |
| UJ-102 | **PASS** | Ask about URL and answer only with retrieved evidence | WEB-004 |
| UJ-105 | **PASS** | Unavailable evidence produces honest failure | WEB-007 |
| UJ-108 | **BLOCKED_ENVIRONMENT** | Live DTF news canary | WEB-011, WEB-012 |

