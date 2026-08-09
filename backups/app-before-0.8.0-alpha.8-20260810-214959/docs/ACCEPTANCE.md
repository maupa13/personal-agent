# Personal Agent Rus 0.2.4 Acceptance

## Release gate (must PASS before ZIP is published)

- STATIC-001 Python/JSON/YAML syntax and package hygiene.
- WIN-001 START/STOP/STATUS/VERIFY/ADMIN/RESTART/REPAIR/LOGS wrappers use explicit named actions and propagate exit codes.
- WIN-002 `pa.ps1` must not use PowerShell automatic `$Args` for Docker arguments.
- WIN-003 Windows-side `VERIFY-PACKAGE.ps1` parses the real lifecycle script and runs its `contract -DryRun` command-binding self-test.
- API-001 public API contains no raw model/provider/container identifiers.
- API-002 admin endpoints reject missing/wrong credentials.
- API-003 invalid user requests return 4xx, not accidental 500s.
- API-004 admin cannot route a mode to a model that is not installed.
- API-005 routing changes affect internal inference but remain hidden from USER.
- API-006 concurrent chat requests succeed.
- API-007 model pull job completes and can be routed.
- API-008 routing persists across Core restart.
- API-009 inference backend outage returns a controlled user-facing 502.
- SEC-001 security headers are present and path traversal is rejected.
- UI-001 desktop USER journey: modes, chat, state persistence.
- UI-002 Product Shell v2: conversation history/search/new-chat/rename/delete/clear/export, Settings, copy/regenerate, safe Markdown/code rendering.
- UI-003 mobile drawer journey has no horizontal overflow and keeps Admin discoverable.
- UI-004 USER UI exposes an authenticated Admin entry but never exposes raw model/provider/container IDs.
- UI-005 ADMIN login, Overview/Routing/Models/System navigation, routing and pull workflow.
- UI-006 model/assistant content cannot inject HTML/JS into USER or ADMIN DOM.
- UI-007 HTML/JS/CSS are `no-store` and versioned so an in-place upgrade cannot silently combine stale UI with a newer Core.
- UI-008 Rus edition short neutral/Russian requests are retried once in Russian if a bootstrap model ignores the language policy.

## Reference Windows runtime gate (must PASS before next product layer)

1. Overlay/update into one canonical directory.
2. Run `START.cmd` without manual Docker commands.
3. Package + Windows command-binding preflight PASS.
4. Ollama container starts.
5. Bootstrap model is reused or downloaded.
6. Personal Agent Core builds/starts.
7. Browser opens only after health + real inference PASS.
8. USER sends messages in Auto/Fast/Smart.
9. ADMIN assigns another installed model to Smart; USER still sees no model ID.
10. `RESTART.cmd` then `VERIFY.cmd` PASS and routing persists.
11. `REPAIR.cmd` PASS without deleting `par-rus-data` or `par-rus-models`.
12. `FULL-ACCEPTANCE.cmd` PASS: real desktop/mobile/admin browser journeys + inference + restart + recovery.
13. `STOP.cmd` then `START.cmd` PASS.

No capability milestone advances while the reference Windows runtime gate is failing.
