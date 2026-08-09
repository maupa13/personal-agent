# Personal Agent Rus 0.7.3 — Distribution Isolation Hotfix

## Scope

Fix canonical-root installation when older releases, evidence folders, IDE metadata, or unrelated files coexist beside the new package.

## Invariants

- `VERIFY-PACKAGE.ps1` verifies checksums and PowerShell syntax only for paths listed in `SHA256SUMS.txt`.
- Unsigned neighboring files never make a valid signed package fail.
- `INSTALL-OR-UPDATE.ps1` stages only signed payload files plus `SHA256SUMS.txt`.
- Signed file corruption still fails checksum verification.
- Manifest absolute paths, `..` traversal, and duplicate paths are rejected.
- Existing `.env`, Docker named volumes, workspace, artifacts, and data remain preserved.

## Windows live gate

The mandatory reference-Windows proof remains: extract over `C:\AI\RusPersonalAgent`, with the known broken v0.7.0 folder still present, then execute `RUN-FIRST.cmd`. Verification must ignore the stale folder and proceed to staged install/runtime repair.
