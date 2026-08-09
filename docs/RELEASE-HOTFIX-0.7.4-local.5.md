# Personal Agent Rus 0.7.4-local.5 — Quality Pass

## Why this build exists

0.7.4-local.4 could start the local product, but the real user journey still exposed three quality defects: Code execution could fail on `/work/<job>/home`, domain-news queries could feed homepage navigation into the model, and chat export/UI were not product-grade.

## Fixed

### Code sandbox

The supervisor keeps job/HOME/TMP/source ownership and grants the unprivileged runner access through the runner group. No `CAP_DAC_OVERRIDE` is added. The worker no longer requires UID ownership transfer for per-job files, which avoids the observed Docker Desktop `EPERM` path.

### Web/news quality

Root-domain news requests use the domain as a search scope. Raw root-homepage text is deferred and only used as a bounded fallback if article evidence cannot be obtained. Extracted text is whitespace-normalized, repeated lines are removed, and giant comma-separated navigation blocks are discarded.

External page data remains an untrusted user-level observation. A system-level Web response policy tells the model to answer the user's question, not echo tool output. Responses beginning with source/tool dumps are retried once; an evidence-only fallback is used if the second synthesis is still unusable.

### Chat export + UI

The current chat has a visible desktop export action and the existing menu action. Export first creates a verified `.md` artifact in the user's workspace and downloads it through the server artifact endpoint; browser Blob download is only a fallback. All-chat export creates a verified `.json` artifact.

User messages are right-aligned and no longer render `Вы` twice. Sources are separate cards rather than part of the answer body.

## Mandatory regressions

- static/package
- distribution/update
- Windows launcher contract
- local launch contract
- API acceptance including WEB-013 and WEB-014
- browser acceptance including FND-CHAT-EXPORT-001
- code-worker acceptance including Docker Desktop permission regression
- orchestrator/deployment/LAN
- billing

Reference-Windows live gates remain authoritative for actual Docker/PowerShell execution on the user's machine.
