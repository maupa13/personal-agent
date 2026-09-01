# Personal Agent

Canonical source tree for the current product lives at the repository root.

Main locations:

- `services/` - runtime services and current application code.
- `tests/` - current acceptance and static checks used by CI.
- `deploy/server/` - VPS deployment files and examples.
- `docs/` - current architecture and operational documentation.

Repository hygiene notes:

- `deploy/server/.env.vps` is local server configuration and must not be committed.
- Historical release snapshots and evidence bundles are not part of the active source tree.
- The repository uses a single canonical source tree at the root. New changes should target `services/`, `tests/`, `deploy/`, and `docs/`.

Common commands:

```sh
python tests/run_acceptance.py
docker compose --env-file deploy/server/.env.vps -f compose.vps.yaml up -d --build
```
