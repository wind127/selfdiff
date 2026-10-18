import json
import pytest
from selfdiff.comparison import compare_periods, challenge, save_snapshot
from selfdiff.exports import export_profile, export_share_card
from selfdiff.analysis.pipeline import execute_run, material_for
from selfdiff.analysis.jobs import get_run
from selfdiff.errors import AppError
from selfdiff.insights import save_insight
from test_analysis import FixedProvider
from test_insights import prepared


def test_unknown_time_excluded_and_empty_period_is_insufficient(db):
    repo, w, draft = prepared(db)
    a = {'start':'2026-01-01T00:00:00+00:00','end':'2026-02-01T00:00:00+00:00'}
    b = {'start':'2026-02-01T00:00:00+00:00','end':'2026-03-01T00:00:00+00:00'}
    assert material_for(repo, dict(a,workspace_id=w)) == []
    rid = compare_periods(repo, {'workspace_id':w}, a, b, '项目启动')
    execute_run(repo, rid, FixedProvider(draft))
    assert get_run(repo,rid)['status'] == 'insufficient'


def test_invalid_periods_rejected(db):
    repo, w, draft = prepared(db)
    with pytest.raises(AppError):
        compare_periods(repo, {'workspace_id':w}, {'start':'tomorrow','end':'yesterday'}, {}, 'test')


def test_export_and_share_are_separate_and_escaped(db):
    repo,w,draft=prepared(db)
    saved=save_insight(repo,'run',draft)
    full=json.loads(export_profile(repo,w,'json'))
    assert full['insights'][0]['evidence'][0]['quote']=='我喜欢先做小版本。'
    card=export_share_card(repo,w,[saved['id']], '<script>alert(1)</script>')
    assert '<script>' not in card and '&lt;script&gt;' in card
    assert '我喜欢先做小版本。' not in card
    assert 'message_id' not in card
    assert b'selfdiff' in export_profile(repo,w,'markdown').lower()


def test_snapshot_and_export_scrub_on_delete(db):
    repo,w,draft=prepared(db)
    save_insight(repo,'run',draft)
    with db.transaction() as c:
        c.execute("UPDATE analysis_runs SET status='succeeded',result=? WHERE id='run'",(json.dumps({'summary':'我的秘密判断'}),))
    sid=save_snapshot(repo,w,'run')
    repo.delete_conversation(w,repo.conversations(w)[0]['id'])
    assert '我的秘密判断' not in export_profile(repo,w,'json').decode()
    with db.transaction() as c:
        assert c.execute('SELECT content FROM profile_snapshots WHERE id=?',(sid,)).fetchone()[0]=='{}'
