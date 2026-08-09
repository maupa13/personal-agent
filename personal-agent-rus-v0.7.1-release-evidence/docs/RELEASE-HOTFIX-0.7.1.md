# Personal Agent Rus v0.7.1

Windows PowerShell 5.1 compatibility hotfix for v0.7.0.

## Root cause

`scripts/pa.ps1` contained an interpolated string with `$Language:`. Windows PowerShell 5.1 parses the colon as part of a variable reference and rejects the script before lifecycle execution.

## Fix

- Replaced `$Language:` with `${Language}:`.
- Added a project-wide regression guard for unsafe `$name:` interpolation in shipped PowerShell scripts.
- `VERIFY-PACKAGE.ps1` now parses every shipped `.ps1`, not only the main lifecycle script.
- Re-ran static, Windows contract, API, browser, billing, orchestrator/deployment and code-worker acceptance suites.

No persistent data or volume format changes are introduced by this hotfix.
