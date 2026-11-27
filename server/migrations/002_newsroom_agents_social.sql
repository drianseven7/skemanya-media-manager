-- Additive newsroom, discovery-agent, research and social publishing foundations.
CREATE TABLE IF NOT EXISTS source_feeds (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(180) NOT NULL,
  feed_url TEXT NOT NULL UNIQUE,
  source_type VARCHAR(40) NOT NULL DEFAULT 'RSS',
  category VARCHAR(120),
  language VARCHAR(12) NOT NULL DEFAULT 'id',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  last_fetched_at TIMESTAMPTZ,
  created_by BIGINT REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_runs (
  id BIGSERIAL PRIMARY KEY,
  agent_key VARCHAR(80) NOT NULL,
  status VARCHAR(24) NOT NULL DEFAULT 'QUEUED',
  query TEXT,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  items_found INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  result_summary TEXT,
  created_by BIGINT REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS research_topics (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  topic_type VARCHAR(80) NOT NULL DEFAULT 'KNOWLEDGE',
  summary TEXT,
  key_facts JSONB NOT NULL DEFAULT '[]'::jsonb,
  sources JSONB NOT NULL DEFAULT '[]'::jsonb,
  verification_status VARCHAR(32) NOT NULL DEFAULT 'NEEDS_REVIEW',
  status VARCHAR(32) NOT NULL DEFAULT 'SAVED',
  created_by BIGINT REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS media_assets (
  id BIGSERIAL PRIMARY KEY,
  filename TEXT NOT NULL,
  mime_type VARCHAR(120) NOT NULL,
  storage_key TEXT NOT NULL UNIQUE,
  byte_size BIGINT NOT NULL DEFAULT 0,
  width INTEGER,
  height INTEGER,
  created_by BIGINT REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS social_accounts (
  id BIGSERIAL PRIMARY KEY,
  platform VARCHAR(32) NOT NULL,
  account_name VARCHAR(180) NOT NULL,
  external_account_id VARCHAR(180) NOT NULL,
  account_type VARCHAR(40),
  token_ciphertext TEXT,
  token_expires_at TIMESTAMPTZ,
  granted_scopes JSONB NOT NULL DEFAULT '[]'::jsonb,
  connection_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  connected_by BIGINT REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(platform, external_account_id)
);

CREATE TABLE IF NOT EXISTS social_publications (
  id BIGSERIAL PRIMARY KEY,
  social_account_id BIGINT REFERENCES social_accounts(id) ON DELETE SET NULL,
  content_id BIGINT REFERENCES content_items(id) ON DELETE SET NULL,
  platform_media_id VARCHAR(180),
  publication_type VARCHAR(32) NOT NULL DEFAULT 'POST',
  caption TEXT,
  media_asset_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  scheduled_at TIMESTAMPTZ,
  published_at TIMESTAMPTZ,
  status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',
  platform_permalink TEXT,
  platform_response JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by BIGINT REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS source_feeds_active_idx ON source_feeds(is_active, updated_at DESC);
CREATE INDEX IF NOT EXISTS agent_runs_created_idx ON agent_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS research_topics_created_idx ON research_topics(created_at DESC);
CREATE INDEX IF NOT EXISTS social_publications_schedule_idx ON social_publications(status, scheduled_at);
