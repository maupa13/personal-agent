# Release Gate — Personal Agent Rus 0.8.0-alpha.7

## Result

**20 authoritative isolated suites: PASS. 0 deterministic FAIL.**

The monolithic release-gate orchestration was interrupted by the external execution harness while entering a browser stage. It is therefore recorded as `INTERRUPTED_EXTERNAL_HARNESS`, not PASS and not a product FAIL. Every mandatory deterministic suite was rerun as an isolated process and completed with exit code 0.

## Alpha.7 additions

- installer version comes from signed `product-manifest.json`;
- VERIFY uses the small bootstrap model and emits native inference timing;
- list/news result target is at least 7 verified items where the source actually provides them;
- no synthetic padding of missing news/products/properties/procurements;
- concrete list and visual cards share one usable evidence set;
- generic news starter uses saved interests or one bounded quick-reply clarification;
- scenario/quick-action selection is mutually exclusive;
- compact/normal/large UI scale;
- progressive answer reveal with reduced-motion fallback.

## External / later gates

- `PERF-A7-WIN-001`: reference Windows bootstrap timing — external.
- `WEB-011`: live DTF canary — external.
- `BILL-LIVE-001`: real YooKassa + HTTPS webhook — external.
- `LAN-LIVE-001`: physical second device — external.
- `PG-RUNTIME-001`: PostgreSQL canonical runtime — beta slice.
- `VPS-EGRESS-001`: RU/global egress routing — 0.9 slice.
- `STREAM-SSE-001`: true token-by-token SSE transport — not claimed by alpha.7; current UX is progressive reveal after the response is received.

## Evidence

See `release-evidence/0.8.0-alpha.7-authoritative/authoritative-summary.json` and referenced suite logs.
