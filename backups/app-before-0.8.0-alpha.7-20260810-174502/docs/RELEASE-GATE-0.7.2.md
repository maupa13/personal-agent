# Release Gate 0.7.2

Scope: canonical Windows distribution + full regression of all capabilities present in 0.7.x.

Mandatory deterministic gates executed before packaging:

- static package checks;
- canonical distribution contract (`DIST-001..003`);
- Windows launcher/Compose binding contract;
- Product Shell browser journeys;
- Auth/Providers/Routing;
- Web/Research;
- Files/Workspace/Artifacts;
- Code sandbox;
- Billing/Entitlements/Usage/Payment adapter;
- Orchestrator/Task Engine;
- VPS deployment contract + public hot-verify contract;
- Monitoring + LAN contract.

Environment-bound gates are not promoted to PASS by CI: real Windows RUN-FIRST/START/REPAIR/lifecycle, physical LAN device, Windows reboot, real VPS/DNS/TLS, real YooKassa merchant payment and clean Windows machine.

Distribution invariant: the user extracts one package anywhere and starts `RUN-FIRST.cmd`; the canonical installed application is `C:\AI\RusPersonalAgent\app`, while stable launchers live directly in `C:\AI\RusPersonalAgent`.
