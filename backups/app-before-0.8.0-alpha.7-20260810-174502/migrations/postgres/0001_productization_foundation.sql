BEGIN;
CREATE TABLE IF NOT EXISTS schema_migrations (
  migration_id TEXT PRIMARY KEY,
  applied_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'USER',
  status TEXT NOT NULL DEFAULT 'active',
  created_at BIGINT NOT NULL,
  updated_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash TEXT UNIQUE NOT NULL,
  created_at BIGINT NOT NULL,
  expires_at BIGINT NOT NULL,
  last_seen_at BIGINT NOT NULL,
  revoked_at BIGINT,
  ip TEXT,
  user_agent TEXT,
  remember_me BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_sessions_user_active ON sessions(user_id, revoked_at, expires_at);

CREATE TABLE IF NOT EXISTS folders (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  created_at BIGINT NOT NULL,
  updated_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_folders_user ON folders(user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS conversations (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  folder_id TEXT,
  title TEXT NOT NULL,
  created_at BIGINT NOT NULL,
  updated_at BIGINT NOT NULL,
  pinned_at BIGINT,
  archived_at BIGINT
);
CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(user_id, archived_at, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_folder ON conversations(user_id, folder_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  sources_json TEXT NOT NULL DEFAULT '[]',
  attachments_json TEXT NOT NULL DEFAULT '[]',
  created_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS user_onboarding (
  user_id TEXT NOT NULL,
  tour_id TEXT NOT NULL,
  tour_version INTEGER NOT NULL,
  status TEXT NOT NULL,
  current_step INTEGER NOT NULL DEFAULT 0,
  completed_at BIGINT,
  updated_at BIGINT NOT NULL,
  PRIMARY KEY(user_id, tour_id)
);

CREATE TABLE IF NOT EXISTS plans (
  id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  price_rub INTEGER NOT NULL,
  support_level TEXT NOT NULL,
  local_unlimited BOOLEAN NOT NULL DEFAULT TRUE,
  remote_token_limit BIGINT NOT NULL DEFAULT 0,
  remote_cost_limit_microrub BIGINT NOT NULL DEFAULT 0,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS plan_entitlements (
  plan_id TEXT NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
  feature_key TEXT NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT FALSE,
  limit_value BIGINT,
  updated_at BIGINT NOT NULL,
  PRIMARY KEY(plan_id, feature_key)
);
CREATE TABLE IF NOT EXISTS subscriptions (
  user_id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL,
  status TEXT NOT NULL,
  period_start BIGINT NOT NULL,
  period_end BIGINT NOT NULL,
  auto_renew BOOLEAN NOT NULL DEFAULT FALSE,
  payment_provider TEXT,
  payment_method_id TEXT,
  cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_plan_status ON subscriptions(plan_id, status);

INSERT INTO schema_migrations(migration_id,applied_at)
VALUES ('0001_productization_foundation', EXTRACT(EPOCH FROM NOW())::BIGINT)
ON CONFLICT(migration_id) DO NOTHING;
COMMIT;
