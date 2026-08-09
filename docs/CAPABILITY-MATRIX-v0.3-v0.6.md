# Personal Agent Rus — Capability Implementation Matrix

Status: SDD / acceptance contract

A capability is visible as `ready` only after its mandatory USER journeys pass.

## User-visible top level

```text
Чат
Веб
Файлы
Код
```

No `· скоро` is removed until the corresponding capability is real.

## Chat

Required:

- persisted conversations;
- new/rename/delete/clear/search/export;
- markdown/code rendering;
- copy/regenerate;
- `Авто/Быстро/Умно`;
- `Объяснить/Написать/Проанализировать` structured presets;
- cancellation/streaming/reconnect in task-engine milestone;
- Russian default for Rus edition;
- provider/model internals hidden from USER.

## Web

Required before `Веб` becomes ready:

- URL intent detection;
- search provider;
- direct static fetch;
- dynamic browser fallback;
- URL normalization;
- SSRF policy;
- redirects revalidated;
- source/evidence records;
- freshness requirement;
- citations;
- prompt-injection isolation;
- deterministic web fixtures;
- live site canaries.

Minimum live canaries:

```text
DTF
Habr
AWS articles
YouTube
ЕГРЮЛ
zakupki.gov.ru
news search
ordinary static page
JS-heavy page
```

External failures use PASS / PRODUCT_FAIL / BLOCKED_EXTERNAL semantics; they are never silently turned into PASS.

## Files

Required before `Файлы` becomes ready:

```text
TXT MD JSON CSV PDF DOCX XLSX PPTX
```

For every supported format:

```text
upload/read
create
physical existence
parse/open validation
content validation
modify
new version
user download
```

Workspace is per-user and allowlisted. User filenames are not trusted filesystem paths.

## Code

Required before `Код` becomes ready:

```text
Python
PowerShell
Java
```

Execution occurs in a dedicated sandbox/worker, never inside Core permissions.

Mandatory controls:

- CPU/RAM/disk/process bounds;
- hard timeout;
- cancellation + process tree termination;
- isolated workspace;
- no Docker socket;
- no DB/provider secrets;
- network disabled by default;
- stdout/stderr/exit code;
- compile/test/repair/retest journey.

## Capability cards

Starter cards are presets, not capabilities:

```text
Объяснить      preset=explain
Написать       preset=write
Проанализировать preset=analyze
```

Capability selector is separate:

```text
Чат  capability=chat
Веб  capability=web
Файлы capability=files
Код  capability=code
```

This separation prevents `smart` or `analyze` from accidentally disabling Web/File/Code execution.
