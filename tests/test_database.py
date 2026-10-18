import sqlite3
import pytest
from selfdiff.store.database import Database


def test_initialize_preserves_existing_data(tmp_path):
    db = Database(tmp_path / 'local.db')
    db.initialize()
    with db.transaction() as conn:
        conn.execute("INSERT INTO workspaces(id,name) VALUES('one','小林')")
    db.initialize()
    with db.transaction() as conn:
        assert conn.execute('SELECT name FROM workspaces').fetchone()[0] == '小林'


def test_transaction_rolls_back(tmp_path):
    db = Database(tmp_path / 'local.db')
    db.initialize()
    with pytest.raises(RuntimeError):
        with db.transaction() as conn:
            conn.execute("INSERT INTO workspaces(id,name) VALUES('one','temporary')")
            raise RuntimeError('abort')
    with db.transaction() as conn:
        assert conn.execute('SELECT count(*) FROM workspaces').fetchone()[0] == 0


def test_foreign_key_prevents_orphan_data(tmp_path):
    db = Database(tmp_path / 'local.db')
    db.initialize()
    with pytest.raises(sqlite3.IntegrityError):
        with db.transaction() as conn:
            conn.execute("INSERT INTO conversations(id,workspace_id,source,external_id,title) VALUES('c','missing','codex','e','t')")
