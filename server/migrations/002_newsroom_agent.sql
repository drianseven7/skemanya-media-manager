CREATE TABLE IF NOT EXISTS source_feeds (
 id BIGSERIAL PRIMARY KEY, name VARCHAR(180) NOT NULL, feed_url TEXT NOT NULL UNIQUE,
 category VARCHAR(120), is_active BOOLEAN NOT NULL DEFAULT TRUE, last_fetched_at TIMESTAMPTZ,
 created_by BIGINT REFERENCES users(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS agent_runs (
 id BIGSERIAL PRIMARY KEY, agent_key VARCHAR(80) NOT NULL, status VARCHAR(24) NOT NULL DEFAULT 'QUEUED',
 query TEXT, started_at TIMESTAMPTZ, finished_at TIMESTAMPTZ, items_found INTEGER NOT NULL DEFAULT 0,
 error_message TEXT, result_summary TEXT, created_by BIGINT REFERENCES users(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS agent_runs_created_idx ON agent_runs(created_at DESC);
