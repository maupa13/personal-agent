# Release Gate — Personal Agent Rus 0.4.0

## Scope

Files / Workspace / Artifacts vertical slice on top of the frozen-by-regression Chat/Auth/Providers/Web foundation.

## Mandatory automated checks

### Formats

- FILE-001 TXT create/read/verify/download
- FILE-002 Markdown create/read/verify/download
- FILE-003 JSON create/read/verify/download
- FILE-004 CSV create/read/verify/download
- FILE-005 text PDF create/read/verify/download
- FILE-006 DOCX create/read/verify/download
- FILE-007 XLSX create/read/verify/download
- FILE-008 PPTX create/read/verify/download

### Upload / artifact lifecycle

- FILE-009 raw upload + untrusted display filename normalization
- FILE-010 malformed/mismatched content fails closed
- FILE-011 edit creates a verified new version
- FILE-012 attached file enters LLM context only through the untrusted file observation boundary
- FILE-013 artifact inventory hides physical storage paths
- FILE-014 cross-user read/download is denied
- FILE-015 Office ZIP path traversal is denied
- FILE-016 oversized upload is rejected before body processing
- FILE-017 real Chromium Files UI journey

## Regression scope

The complete existing foundation must remain green:

```text
static
Windows command contract
Chat/presets
Auth
Provider Registry/routing
Web/Search/URL/Research
SSRF/prompt-injection boundary
concurrency
persistence
Product Shell desktop/mobile/Admin/XSS
```

## Environment-bound gates

The local build environment does not promote the following to PASS:

- real reference-Windows Docker lifecycle;
- real-model live Chromium journey;
- DTF live canary when external connectivity is unavailable;
- Windows reboot;
- clean Windows machine.

Those retain formal `BLOCKED_ENVIRONMENT`/external status until executed on the required target.

## Explicit non-features

These stay `NOT_IMPLEMENTED` and must not be shown as ready:

- scanned PDF OCR;
- ZIP/TAR as user artifacts;
- image/audio/video file understanding;
- Code execution;
- cloud object-storage migration;
- long-document RAG/indexing.
