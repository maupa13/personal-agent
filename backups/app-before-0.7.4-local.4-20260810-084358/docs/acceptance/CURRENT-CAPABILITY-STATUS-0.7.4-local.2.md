# Current capability status — 0.7.4-local.3

This build is a **quality local-launch candidate**, not `1.0 RELEASE PASS`.

## Local baseline

- Core/UI: ready by deterministic contract.
- Local Ollama inference: required for local readiness.
- SearXNG + Browser: required local Web baseline.
- Files/Artifacts: ready by deterministic acceptance.
- Code sandbox: isolated and covered deterministically; it degrades independently during normal start, while strict Code acceptance remains mandatory for a Code PASS.
- Auth/Providers/Billing/Tasks/Monitoring/LAN contracts: deterministic PASS.

## Release truth

`1.0 RELEASE PASS` remains forbidden until the full MASTER-SPEC/user-journey matrix and environment-bound Windows/VPS/payment/LAN gates have real evidence. This build deliberately optimizes the next step: reliable local Windows startup without allowing one optional worker to take down the whole user-facing product.
