# PostgreSQL server foundation

`compose.postgres-foundation.yaml` provisions PostgreSQL and the server Core image/driver for the upcoming server persistence migration.

Important: in 0.8.0-alpha.2 the canonical Core repositories still use SQLite. `PA_DATABASE_URL` is validated and exposed only as a readiness/configuration signal. Do not call this profile production PostgreSQL until `PG-RUNTIME-001` and migration/rollback gates pass.

The purpose of this slice is to freeze:
- PostgreSQL image/version;
- driver dependency;
- initial schema and indexes;
- named-volume ownership;
- server configuration contract;
- a deterministic migration target for the next slice.
