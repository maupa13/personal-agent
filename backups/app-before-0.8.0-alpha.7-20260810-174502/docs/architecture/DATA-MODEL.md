# Data Model

Current prototype persists provider/routing/auth state in SQLite. Target production: PostgreSQL + Redis-compatible coordination + object storage. Required domain entities from MASTER-SPEC include tenants/users/sessions, conversations/messages, tasks/steps/events, workspaces/files/artifacts, providers/models/credentials, connectors, automations, usage and audit.
