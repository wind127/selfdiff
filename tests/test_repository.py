import json
import pytest
from selfdiff.store.repository import Repository
from selfdiff.sources.ingest import preview_upload, preview_path
from selfdiff.errors import AppError


def sample(text='我喜欢先做小版本。', cid='c', role='user', timestamp=None):
    return json.dumps({'conversations': [{'id': cid, 'title': '小项目', 'messages': [
        {'id': 'u', 'role': role, 'content': text, 'timestamp': timestamp}]}]}, ensure_ascii=False).encode()


def test_idempotency_versions_and_distinct_sessions(db):
    repo = Repository(db)
    wid = repo.create_workspace('我的资料')['id']
    one = preview_upload('normalized', 'a.json', sample())
    assert repo.import_preview(wid, one)['added_messages'] == 1
    assert repo.import_preview(wid, one)['added_messages'] == 0
    repo.import_preview(wid, preview_upload('normalized', 'a.json', sample('我更喜欢先访谈。')))
    msg = repo.messages(wid)[0]
    assert msg['version'] == 2
    assert repo.message(wid, msg['id'], 1)['text'] == '我喜欢先做小版本。'
    repo.import_preview(wid, preview_upload('normalized', 'b.json', sample(cid='other')))
    assert len(repo.conversations(wid)) == 2


def test_literal_search_and_workspace_boundary(db):
    repo = Repository(db)
    a, b = [repo.create_workspace(n)['id'] for n in ['a', 'b']]
    repo.import_preview(a, preview_upload('normalized', 'a.json', sample('我写了 100%_done。')))
    assert len(repo.messages(a, '%_')) == 1
    assert repo.messages(b) == []
    with pytest.raises(AppError):
        repo.delete_conversation(b, repo.conversations(a)[0]['id'])


def test_delete_clears_messages_and_increments_version(db):
    repo = Repository(db)
    w = repo.create_workspace('w')['id']
    repo.import_preview(w, preview_upload('normalized', 'a.json', sample()))
    before = repo.workspace(w)['data_version']
    repo.delete_conversation(w, repo.conversations(w)[0]['id'])
    assert repo.messages(w) == []
    assert repo.workspace(w)['data_version'] > before


def test_preview_changed_path_cannot_import_and_failure_is_atomic(db, tmp_path):
    repo = Repository(db)
    w = repo.create_workspace('w')['id']
    path = tmp_path / '中文.json'
    path.write_bytes(sample())
    preview = preview_path('normalized', path)
    path.write_bytes(sample('我改变了输入。'))
    with pytest.raises(AppError):
        repo.import_preview(w, preview)
    assert repo.messages(w) == []
