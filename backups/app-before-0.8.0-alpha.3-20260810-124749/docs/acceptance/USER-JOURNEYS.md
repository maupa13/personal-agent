# User Journey Registry — v0.7.3

Generated from `tests/user-journeys-registry.json`. The JSON registry is authoritative.

| ID | Capability | Status | Journey |
|---|---|---|---|
| UJ-001 | foundation | **PASS** | Fresh package start |
| UJ-010 | chat | **PASS** | First chat with real inference |
| UJ-011 | chat | **PASS** | Refresh and continue conversation |
| UJ-014 | chat | **PASS** | Switch Auto/Fast/Smart modes |
| UJ-020 | auth | **PASS** | Registration/login/session |
| UJ-021 | providers | **PASS** | Discover local provider models |
| UJ-022 | providers | **PASS** | Connect OpenAI-compatible provider and discover models |
| UJ-023 | providers | **PASS** | Assign provider+model routing and persist |
| UJ-100 | web | **PASS** | Search Web and show normalized results |
| UJ-101 | web | **PASS** | Read a specific URL through static/browser pipeline |
| UJ-102 | web | **PASS** | Ask about URL and answer only with retrieved evidence |
| UJ-103 | research | **PASS** | Ask for current news and automatically invoke Web |
| UJ-104 | research | **PASS** | Multi-source research with sources |
| UJ-105 | web | **PASS** | Unavailable evidence produces honest failure |
| UJ-106 | security | **PASS** | Web SSRF/private redirect attack is blocked |
| UJ-107 | security | **PASS** | Malicious Web prompt injection remains untrusted data |
| UJ-108 | web | **BLOCKED_ENVIRONMENT** | Live DTF news canary |
| UJ-150 | context-memory | **NOT_IMPLEMENTED** | 50+ message coherent conversation |
| UJ-151 | context-memory | **NOT_IMPLEMENTED** | Context compression respects model window |
| UJ-152 | context-memory | **NOT_IMPLEMENTED** | Restart restores conversation semantics |
| UJ-153 | context-memory | **NOT_IMPLEMENTED** | User views/edits/deletes memory |
| UJ-154 | context-memory | **NOT_IMPLEMENTED** | Large document selective retrieval |
| UJ-155 | context-memory | **NOT_IMPLEMENTED** | Model context switch without overflow |
| UJ-200 | files | **PASS** | Upload/read/analyze TXT |
| UJ-201 | files | **PASS** | Upload/read/analyze MD |
| UJ-202 | files | **PASS** | Upload/read/analyze JSON |
| UJ-203 | files | **PASS** | Upload/read/analyze CSV |
| UJ-204 | files | **PASS** | Upload/read/analyze PDF text |
| UJ-205 | files | **NOT_IMPLEMENTED** | Upload/read/analyze PDF scan/OCR |
| UJ-206 | files | **PASS** | Upload/read/analyze DOCX |
| UJ-207 | files | **PASS** | Upload/read/analyze XLSX |
| UJ-208 | files | **PASS** | Upload/read/analyze PPTX |
| UJ-209 | files | **NOT_IMPLEMENTED** | Upload/read/analyze ZIP |
| UJ-210 | files | **NOT_IMPLEMENTED** | Upload/read/analyze image |
| UJ-211 | files | **NOT_IMPLEMENTED** | Upload/read/analyze audio |
| UJ-212 | files | **NOT_IMPLEMENTED** | Upload/read/analyze video |
| UJ-213 | files | **NOT_IMPLEMENTED** | Upload/read/analyze Java |
| UJ-214 | files | **NOT_IMPLEMENTED** | Upload/read/analyze Python |
| UJ-215 | files | **NOT_IMPLEMENTED** | Upload/read/analyze PowerShell |
| UJ-220 | files-artifacts | **NOT_IMPLEMENTED** | Create validated artifact |
| UJ-221 | files-artifacts | **NOT_IMPLEMENTED** | Edit existing artifact and preserve unrelated content |
| UJ-222 | files-artifacts | **NOT_IMPLEMENTED** | Download artifact with authorization |
| UJ-223 | files-artifacts | **NOT_IMPLEMENTED** | Malformed file controlled failure |
| UJ-224 | files-artifacts | **NOT_IMPLEMENTED** | Large file resource policy |
| UJ-225 | files-artifacts | **NOT_IMPLEMENTED** | Archive zip-slip/bomb protection |
| UJ-226 | files-artifacts | **NOT_IMPLEMENTED** | Multi-artifact XLSX + PDF report |
| UJ-300 | code-data | **NOT_IMPLEMENTED** | Python generate/execute/test |
| UJ-301 | code-data | **NOT_IMPLEMENTED** | PowerShell generate/execute/test |
| UJ-302 | code-data | **NOT_IMPLEMENTED** | Java project discover/modify/compile/JUnit/retest |
| UJ-303 | code-data | **NOT_IMPLEMENTED** | Failing tests diagnose/fix/regression |
| UJ-304 | code-data | **NOT_IMPLEMENTED** | Code timeout and cancellation |
| UJ-305 | code-data | **NOT_IMPLEMENTED** | Sandbox filesystem escape blocked |
| UJ-306 | code-data | **NOT_IMPLEMENTED** | Sandbox Docker socket/secrets blocked |
| UJ-320 | code-data | **NOT_IMPLEMENTED** | CSV/XLSX data clean/transform/visualize |
| UJ-321 | code-data | **NOT_IMPLEMENTED** | SQL schema/query/optimization |
| UJ-322 | code-data | **NOT_IMPLEMENTED** | ETL API + file + database |
| UJ-400 | image | **NOT_IMPLEMENTED** | Image upload and vision analysis |
| UJ-401 | image | **NOT_IMPLEMENTED** | Image generation artifact |
| UJ-402 | image | **NOT_IMPLEMENTED** | Image edit/inpainting/upscale |
| UJ-420 | audio | **NOT_IMPLEMENTED** | Audio transcription with timestamps |
| UJ-421 | audio | **NOT_IMPLEMENTED** | Diarization/summary/action items |
| UJ-422 | audio | **NOT_IMPLEMENTED** | TTS playable output |
| UJ-440 | video | **NOT_IMPLEMENTED** | Video transcript/scenes/keyframes/OCR/summary |
| UJ-500 | connectors | **NOT_IMPLEMENTED** | REST connector read |
| UJ-501 | connectors | **NOT_IMPLEMENTED** | OAuth connect/refresh/revoke |
| UJ-502 | connectors | **NOT_IMPLEMENTED** | Read-only connector cannot write |
| UJ-503 | connectors | **NOT_IMPLEMENTED** | External write requires permission |
| UJ-504 | connectors | **NOT_IMPLEMENTED** | Connector outage gives PARTIAL/BLOCKED |
| UJ-520 | connectors | **NOT_IMPLEMENTED** | MCP server capability discovery |
| UJ-521 | connectors | **NOT_IMPLEMENTED** | Plugin manifest permissions |
| UJ-540 | automation | **NOT_IMPLEMENTED** | One-time scheduled task |
| UJ-541 | automation | **NOT_IMPLEMENTED** | Recurring timezone-aware task |
| UJ-542 | automation | **NOT_IMPLEMENTED** | Condition-based monitor |
| UJ-543 | automation | **NOT_IMPLEMENTED** | Restart recovers schedules without duplicates |
| UJ-544 | automation | **NOT_IMPLEMENTED** | Automation notification delivery |
| UJ-600 | account-security | **NOT_IMPLEMENTED** | Email verification according to policy |
| UJ-601 | account-security | **NOT_IMPLEMENTED** | Password reset single-use expiry |
| UJ-602 | account-security | **NOT_IMPLEMENTED** | Session list and revoke |
| UJ-603 | account-security | **NOT_IMPLEMENTED** | 2FA/TOTP and backup codes |
| UJ-604 | account-security | **NOT_IMPLEMENTED** | Personal cabinet profile/privacy/memory/storage |
| UJ-605 | account-security | **NOT_IMPLEMENTED** | Data export and delete account |
| UJ-620 | billing | **PASS** | Plan entitlement enforcement |
| UJ-621 | billing | **PASS** | Usage metering per model/provider |
| UJ-622 | billing | **PASS** | Payment success + idempotent webhook |
| UJ-623 | billing | **NOT_IMPLEMENTED** | Upgrade/downgrade/grace/cancel |
| UJ-624 | billing | **PASS** | BYOK usage separated from platform cost |
| UJ-625 | billing | **PASS** | Quota exhaustion local/private fallback |
| UJ-640 | public-api | **NOT_IMPLEMENTED** | User API key create/use/revoke |
| UJ-641 | public-api | **NOT_IMPLEMENTED** | Inbound OpenAI-compatible chat |
| UJ-642 | public-api | **NOT_IMPLEMENTED** | Rate limit by user/tenant/key |
| UJ-660 | admin-ops | **NOT_IMPLEMENTED** | Admin user suspend/unsuspend/plan/quota |
| UJ-661 | admin-ops | **NOT_IMPLEMENTED** | Admin provider health/priority/pricing/privacy |
| UJ-662 | admin-ops | **NOT_IMPLEMENTED** | Admin queues/workers/storage/health |
| UJ-663 | admin-ops | **NOT_IMPLEMENTED** | Audit log sensitive admin actions |
| UJ-700 | lifecycle | **NOT_IMPLEMENTED** | STOP -> START preserves state |
| UJ-701 | lifecycle | **NOT_IMPLEMENTED** | RESTART preserves state |
| UJ-702 | lifecycle | **NOT_IMPLEMENTED** | REPAIR healthy is idempotent |
| UJ-703 | lifecycle | **NOT_IMPLEMENTED** | REPAIR damaged runtime preserves data |
| UJ-704 | lifecycle | **NOT_IMPLEMENTED** | Backup -> restore verified |
| UJ-705 | lifecycle | **NOT_IMPLEMENTED** | Update -> migrate -> verify |
| UJ-706 | lifecycle | **NOT_IMPLEMENTED** | Failed update rollback including data |
| UJ-707 | lifecycle | **NOT_IMPLEMENTED** | Real Windows reboot recovery |
| UJ-708 | lifecycle | **NOT_IMPLEMENTED** | Clean machine bootstrap |
| UJ-730 | security | **NOT_IMPLEMENTED** | Tenant IDOR blocked |
| UJ-731 | security | **NOT_IMPLEMENTED** | CSRF blocked |
| UJ-732 | security | **NOT_IMPLEMENTED** | XSS blocked |
| UJ-733 | security | **NOT_IMPLEMENTED** | SQL injection blocked |
| UJ-734 | security | **NOT_IMPLEMENTED** | Prompt injection blocked |
| UJ-735 | security | **NOT_IMPLEMENTED** | Secret leakage attempt blocked |
| UJ-736 | security | **NOT_IMPLEMENTED** | Upload abuse blocked |
| UJ-737 | security | **NOT_IMPLEMENTED** | Rate-limit abuse handled |
| UJ-760 | mobile | **NOT_IMPLEMENTED** | Mobile registration/login/chat |
| UJ-761 | mobile | **NOT_IMPLEMENTED** | Mobile file/image/audio upload |
| UJ-762 | mobile | **NOT_IMPLEMENTED** | Mobile artifact download |
| UJ-763 | mobile | **NOT_IMPLEMENTED** | Real mobile microphone secure-context journey |
| UJ-764 | mobile | **NOT_IMPLEMENTED** | PWA install/share/push readiness |
| UJ-800 | multi-capability | **NOT_IMPLEMENTED** | Research -> XLSX -> PDF with verified sources/artifacts |
| UJ-801 | multi-capability | **NOT_IMPLEMENTED** | Uploaded document -> research -> revised document |
| UJ-802 | multi-capability | **NOT_IMPLEMENTED** | Web -> code -> validated artifact |
| UJ-803 | multi-capability | **NOT_IMPLEMENTED** | External API read -> compare file -> permission -> external write |
| UJ-216 | files | **PASS** | Create verified artifact in supported format and download it |
| UJ-217 | files | **PASS** | Modify artifact as a verified new version |
| UJ-218 | files | **PASS** | Workspace/artifact isolation between accounts |
| UJ-219 | files-security | **PASS** | Reject malformed, oversized and path-traversal file inputs |
| UJ-290 | code.execute | **PASS** | Run Python snippet in isolated sandbox and inspect stdout/stderr/exit code |
| UJ-291 | code.execute | **PASS** | Compile and run Java 21 snippet in isolated sandbox |
| UJ-292 | code.execute | **PASS** | Run PowerShell snippet through sandbox command contract |
| UJ-293 | code.execute | **PASS** | Compilation/non-zero process failure is surfaced, never reported as success |
| UJ-294 | code.execute | **PASS** | Timeout and cancellation terminate sandbox process tree |
| UJ-295 | code-security | **PASS** | Execution output is bounded and runtime secrets are not inherited by user code |
| UJ-296 | code-security | **PASS** | Sandbox has no network/Docker socket and uses read-only bounded runtime |
| UJ-297 | code-security | **PASS** | Code job ownership is isolated between accounts |
| UJ-298 | code.execute | **BLOCKED_ENVIRONMENT** | Reference Windows Docker image executes real Python, Java and PowerShell |
| UJ-626 | billing | **PASS** | User opts in to token usage display; default remains hidden |
| UJ-627 | billing | **BLOCKED_ENVIRONMENT** | Real YooKassa merchant checkout/webhook/recurring payment on public HTTPS |
| UJ-403 | orchestrator | **PASS** | User cancels a running/recoverable task |
| UJ-650 | deployment | **PASS** | Admin saves VPS target with trusted SSH fingerprint and no persisted credential |
| UJ-651 | deployment | **PASS** | Admin preflight recommends server-lite for weak VPS |
| UJ-652 | deployment | **PASS** | Staged VPS deploy keeps current/previous and performs hot verification |
| UJ-653 | deployment | **PASS** | Admin rollback switches to previous VPS release |
| UJ-654 | observability | **PASS** | Admin sees lightweight runtime monitoring on weak/local node |
| UJ-655 | lan | **PASS** | Windows owner enables/disables Private-LAN access without deleting data |
| UJ-656 | deployment | **BLOCKED_ENVIRONMENT** | Real VPS deploy + DNS/HTTPS + remote provider + browser chat |
| UJ-657 | lan | **BLOCKED_ENVIRONMENT** | Physical second device uses local Docker UI over LAN |
| UJ-658 | deployment | **PASS** | Admin prepares a fresh Debian/Ubuntu VPS with Docker/Compose using root SSH |
| UJ-659 | deployment-security | **PASS** | Public server account sessions use Secure cookies and reject state changes without CSRF |
