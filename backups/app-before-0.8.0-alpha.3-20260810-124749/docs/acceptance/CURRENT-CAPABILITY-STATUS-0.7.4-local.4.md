# Current capability status — 0.7.4-local.4

This build is a **quality local-launch candidate**, not `1.0 RELEASE PASS`.

## Local baseline

- Core/UI: ready by deterministic contract; real Windows Core startup already reached PASS in the previous reference run.
- Local Ollama inference: required; real reference inference already reached PASS.
- SearXNG + Browser: required local Web baseline; reference startup reached PASS.
- Files/Artifacts: deterministic acceptance PASS.
- Code Worker startup/runtime inventory: reference Windows PASS.
- Code execution: patched for the capability-restricted job-directory permission defect; must be re-proven on the reference Windows Docker runtime.
- Auth/Providers/Billing/Tasks/Monitoring/LAN contracts: deterministic PASS.

## Degradation contract

A Code execution failure cannot take down Chat/Web/Research/Files during normal start. Code becomes `DEGRADED` and the launcher still reaches the user-facing UI. Strict Code/full/release acceptance remains mandatory for a Code/release PASS.

## Release truth

`1.0 RELEASE PASS` remains forbidden until the full MASTER-SPEC/user-journey matrix and environment-bound Windows/VPS/payment/LAN gates have real evidence.
