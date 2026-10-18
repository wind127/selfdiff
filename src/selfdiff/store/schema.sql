PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS workspaces (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, demo INTEGER NOT NULL DEFAULT 0,
 data_version INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS sources (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
 kind TEXT NOT NULL, label TEXT NOT NULL, UNIQUE(workspace_id,kind,label));
CREATE TABLE IF NOT EXISTS conversations (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
 source TEXT NOT NULL, external_id TEXT NOT NULL, title TEXT NOT NULL, branch_id TEXT,
 UNIQUE(workspace_id,source,external_id), UNIQUE(id,workspace_id));
CREATE TABLE IF NOT EXISTS messages (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, conversation_id TEXT NOT NULL,
 external_id TEXT NOT NULL, role TEXT NOT NULL, content_kind TEXT NOT NULL DEFAULT 'uncertain',
 occurred_at TEXT, active_version INTEGER NOT NULL DEFAULT 1,
 UNIQUE(conversation_id,external_id), UNIQUE(id,workspace_id),
 FOREIGN KEY(conversation_id,workspace_id) REFERENCES conversations(id,workspace_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS message_versions (
 message_id TEXT NOT NULL, workspace_id TEXT NOT NULL, version INTEGER NOT NULL,
 text TEXT NOT NULL, digest TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'unknown',
 content_kind TEXT NOT NULL DEFAULT 'uncertain', occurred_at TEXT, PRIMARY KEY(message_id,version),
 UNIQUE(message_id,version,workspace_id),
 FOREIGN KEY(message_id,workspace_id) REFERENCES messages(id,workspace_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS import_runs (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
 summary TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS analysis_runs (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
 mode TEXT NOT NULL, status TEXT NOT NULL, data_version INTEGER NOT NULL, scope TEXT NOT NULL,
 total_batches INTEGER NOT NULL DEFAULT 0, completed_batches INTEGER NOT NULL DEFAULT 0,
 rejected_candidates INTEGER NOT NULL DEFAULT 0, error TEXT, result TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS analysis_batches (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
 run_id TEXT NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
 input_hash TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS insights (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
 run_id TEXT REFERENCES analysis_runs(id), pattern_key TEXT NOT NULL, dimension TEXT NOT NULL,
 kind TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', revision INTEGER NOT NULL DEFAULT 0,
 content TEXT NOT NULL, invalidated INTEGER NOT NULL DEFAULT 0,
 UNIQUE(workspace_id,pattern_key), UNIQUE(id,workspace_id));
CREATE TABLE IF NOT EXISTS evidence (
 id TEXT PRIMARY KEY, insight_id TEXT NOT NULL REFERENCES insights(id) ON DELETE CASCADE,
 workspace_id TEXT NOT NULL, message_id TEXT NOT NULL, version INTEGER NOT NULL,
 quote TEXT NOT NULL, relation TEXT NOT NULL,
 FOREIGN KEY(message_id,version,workspace_id) REFERENCES message_versions(message_id,version,workspace_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS insight_revisions (
 id TEXT PRIMARY KEY, insight_id TEXT NOT NULL REFERENCES insights(id) ON DELETE CASCADE,
 version INTEGER NOT NULL, verdict TEXT NOT NULL, text TEXT NOT NULL, reason TEXT NOT NULL,
 origin TEXT NOT NULL DEFAULT 'user_revision', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(insight_id,version));
CREATE TABLE IF NOT EXISTS profile_snapshots (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
 run_id TEXT REFERENCES analysis_runs(id), content TEXT NOT NULL, invalidated INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS provider_settings (
 workspace_id TEXT PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
 base_url TEXT NOT NULL, model TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS messages_workspace ON messages(workspace_id,conversation_id);
CREATE INDEX IF NOT EXISTS insights_workspace ON insights(workspace_id,status);
