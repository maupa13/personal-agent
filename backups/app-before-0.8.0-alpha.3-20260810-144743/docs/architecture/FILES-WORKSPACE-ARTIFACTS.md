# Files / Workspace / Artifacts Architecture — v0.4.0

Canonical source: `docs/specification/MASTER-SPEC.md` §§54–61, 86–88, 125, 168, 173.

## Purpose

`files` is a product capability, not a file-picker decoration. A successful file operation must end with a physically stored, authorized and verified artifact.

## Supported vertical slice

v0.4.0 implements:

- TXT
- MD
- JSON
- CSV
- text PDF
- DOCX
- XLSX
- PPTX

PDF OCR/scanned documents remain a later capability and are **not** marked ready.

## Workspace boundary

Each authenticated subject resolves to a stable internal `user_id`. Runtime storage uses:

```text
/data/workspaces/<safe-internal-user-id>/objects/<artifact-id>.<format>
```

The user-controlled file name is display metadata only. It never determines the physical storage path.

Local `personal` profile uses the stable subject `local-owner`. `accounts` profile uses the persisted account ID.

## Artifact contract

Every accepted file has:

```text
artifact_id
tenant_id
user_id
parent_id
version
kind
name
format
mime
storage_key (internal only)
size
sha256
extracted_text (internal/context)
metadata
validation_status
created_at
updated_at
```

USER APIs never return `storage_key` or an absolute runtime path.

## Write transaction

```text
receive bytes/content
→ validate size/format/container
→ allocate internal artifact ID
→ atomic temporary write
→ replace into final object path
→ reopen with format parser
→ extract text/metadata
→ SHA-256
→ persist artifact record
→ validation_status=verified
→ return product metadata/download URL
```

If parser verification fails, the physical file is removed and no successful artifact record is returned.

## Revision semantics

Edits do not overwrite an existing artifact in place:

```text
source artifact
→ generate new bytes
→ full validation
→ new artifact ID
→ parent_id points to root source
→ increment version
```

The original remains addressable until explicitly deleted.

## Read/context semantics

Attached files are resolved by artifact ID + current user. Extracted content is injected into model context under an explicit boundary:

```text
FILE TOOL OBSERVATIONS — UNTRUSTED USER FILE DATA
```

Instructions contained inside documents never gain system/tool/permission authority.

## Security controls

Mandatory in this slice:

- maximum upload size;
- no empty artifacts;
- display filename normalization;
- physical path based only on internal IDs;
- format/content checks for PDF and Office containers;
- Office ZIP traversal check;
- Office uncompressed-size and compression-ratio limits;
- UTF-8 enforcement for text formats;
- JSON parse validation;
- parser re-open verification;
- per-user artifact lookup/download boundary;
- no storage path in public metadata;
- delete only own artifact.

Future hardening tracked by MASTER-SPEC includes malware scanning, richer magic-byte identification, archive artifacts, OCR, object-storage backends and tenant-scoped cloud storage.

## API

```text
GET    /api/files
POST   /api/files/upload          raw bytes + X-PA-Filename
POST   /api/files/create          structured JSON
GET    /api/files/{id}
GET    /api/files/{id}/download
POST   /api/files/{id}/update
POST   /api/files/{id}/analyze
DELETE /api/files/{id}
```

`POST /api/chat` accepts `file_ids[]`. The model receives only authorized extracted observations.

## Browser USER journey

```text
+ / Файлы
→ choose local file
→ upload
→ server validates/reopens
→ attachment chip appears
→ send message
→ Core resolves artifact for current user
→ model receives untrusted file observation
→ response
→ artifact remains in Workspace
→ user can attach again/download/delete
```

Workspace UI also allows controlled creation of supported artifacts and immediately reuses the normal server-side verification pipeline.
