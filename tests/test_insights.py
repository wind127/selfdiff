import json
import pytest
from selfdiff.evidence import validate_evidence
from selfdiff.insights import save_insight, revise_insight, list_insights
from selfdiff.store.repository import Repository
from selfdiff.sources.ingest import preview_upload
from selfdiff.errors import AppError
from test_repository import sample


def prepared(db):
    repo = Repository(db)
    w = repo.create_workspace('测试')['id']
    for cid in ['one', 'two']:
        repo.import_preview(w, preview_upload('normalized', 'a.json', sample(cid=cid)))
    with db.transaction() as c:
        c.execute("INSERT INTO analysis_runs(id,workspace_id,mode,status,data_version,scope) VALUES('run',?,'profile','running',2,'{}')", (w,))
    refs = [dict(message_id=m['id'], version=1, quote='我喜欢先做小版本。', relation='support') for m in repo.messages(w)]
    draft = dict(pattern_key='small-start', dimension='action_results', kind='success_condition', title='小步开始', observation='两次明确选择先做小版本。', context='启动新项目时', alternatives=['也可能是这两次时间有限。'], question='其他场景也适用吗？', evidence=refs)
    return repo, w, draft


def test_exact_quotes_roles_and_versions(db):
    repo, w, draft = prepared(db)
    assert validate_evidence(repo, w, draft['evidence'])['valid']
    for field, value in [('quote', '完全不存在'), ('quote', '  '), ('version', 999), ('message_id', 'missing')]:
        bad = dict(draft['evidence'][0], **{field: value})
        assert not validate_evidence(repo, w, [bad])['valid']
    repo.import_preview(w, preview_upload('normalized', 'a.json', sample(cid='assistant', role='assistant')))
    assistant = next(m for m in repo.messages(w) if m['role'] == 'assistant')
    assert not validate_evidence(repo, w, [dict(message_id=assistant['id'],version=1,quote=assistant['text'],relation='support')])['valid']


def test_single_conversation_cannot_be_recurring(db):
    repo, w, draft = prepared(db)
    draft['evidence'] = draft['evidence'][:1]
    assert not save_insight(repo, 'run', draft)['accepted']


def test_rejected_insight_does_not_revive_and_revisions_conflict(db):
    repo, w, draft = prepared(db)
    saved = save_insight(repo, 'run', draft)
    assert saved['accepted']
    revised = revise_insight(repo, w, saved['id'], 'rejected', '只限于赶时间的项目。', '背景不同', 0)
    assert revised['origin'] == 'user_revision'
    with pytest.raises(AppError) as exc:
        revise_insight(repo, w, saved['id'], 'confirmed', '覆盖', '', 0)
    assert exc.value.status == 409
    assert not save_insight(repo, 'run', draft)['accepted']
    assert list_insights(repo, w) == []


def test_delete_scrubs_generated_text_and_old_job_cannot_write(db):
    repo, w, draft = prepared(db)
    saved = save_insight(repo, 'run', draft)
    revise_insight(repo, w, saved['id'], 'confirmed', '我的修订', '理由', 0)
    repo.delete_conversation(w, repo.conversations(w)[0]['id'])
    assert list_insights(repo, w) == []
    assert not save_insight(repo, 'run', draft)['accepted']
    with db.transaction() as c:
        assert c.execute('SELECT count(*) FROM insight_revisions').fetchone()[0] == 0
        assert all(r[0] == '{}' for r in c.execute('SELECT content FROM insights'))


def test_quoted_and_hypothetical_material_not_personal_evidence(db):
    repo, w, draft = prepared(db)
    repo.import_preview(w, preview_upload('normalized', 'q.json', sample('假设我是一名医生。', cid='q')))
    m = next(m for m in repo.messages(w) if m['text'].startswith('假设'))
    ref = dict(message_id=m['id'],version=1,quote=m['text'],relation='support')
    assert not validate_evidence(repo,w,[ref])['valid']
