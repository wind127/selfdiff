from contextlib import contextmanager
from pathlib import Path
import sqlite3


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)

    @contextmanager
    def transaction(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA busy_timeout=15000')
        try:
            conn.execute('BEGIN IMMEDIATE')
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.executescript(Path(__file__).with_name('schema.sql').read_text(encoding='utf-8'))
            if 'active' not in {r[1] for r in conn.execute('PRAGMA table_info(messages)')}:
                conn.execute('ALTER TABLE messages ADD COLUMN active INTEGER NOT NULL DEFAULT 1')
            columns = {r[1] for r in conn.execute('PRAGMA table_info(message_versions)')}
            for column, definition in [('role', "TEXT NOT NULL DEFAULT 'unknown'"), ('content_kind', "TEXT NOT NULL DEFAULT 'uncertain'"), ('occurred_at', 'TEXT')]:
                if column not in columns:
                    conn.execute(f'ALTER TABLE message_versions ADD COLUMN {column} {definition}')
            if 'role' not in columns:
                # Only the current version has recoverable speaker metadata in early local builds.
                conn.execute('UPDATE message_versions SET role=(SELECT role FROM messages WHERE id=message_id),content_kind=(SELECT content_kind FROM messages WHERE id=message_id),occurred_at=(SELECT occurred_at FROM messages WHERE id=message_id) WHERE version=(SELECT active_version FROM messages WHERE id=message_id)')
