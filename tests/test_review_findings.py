import json
import pytest
from selfdiff.store.repository import Repository, encoded
from selfdiff.sources.ingest import preview_upload
from selfdiff.insights import list_insights,save_insight,revise_insight
from selfdiff.analysis.pipeline import execute_run
from selfdiff.analysis.jobs import create_run,get_run
from selfdiff.comparison import save_snapshot
from selfdiff.exports import export_profile
from selfdiff.errors import AppError
from test_insights import prepared
from test_analysis import FixedProvider
from test_repository import sample


def branch(selected):
    def node(parent,text):
        return {'parent':parent,'message':{'author':{'role':'user'},'content':{'parts':[text]}}}
    return json.dumps([{'id':'tree','title':'分支','current_node':selected,'mapping':{
        'root':node(None,'我正在选择方案。'),'a':node('root','我选择 A。'),'b':node('root','我选择 B。')}}]).encode()


def test_branch_switch_replaces_current_membership(db):
    repo=Repository(db);w=repo.create_workspace('w')['id']
    repo.import_preview(w,preview_upload('chatgpt','conversations.json',branch('a')))
    old=next(m for m in repo.messages(w) if m['text']=='我选择 A。')
    repo.import_preview(w,preview_upload('chatgpt','conversations.json',branch('b')))
    assert {m['text'] for m in repo.messages(w)}=={'我正在选择方案。','我选择 B。'}
    assert repo.message(w,old['id'],1)['text']=='我选择 A。'


def test_run_cannot_cite_old_version_outside_current_selection(db):
    repo=Repository(db);w=repo.create_workspace('w')['id']
    repo.import_preview(w,preview_upload('normalized','a.json',sample('我去年先规划。',timestamp='2025-01-05T00:00:00Z')))
    m=repo.messages(w)[0]
    repo.import_preview(w,preview_upload('normalized','a.json',sample('我今年先动手。',timestamp='2026-01-05T00:00:00Z')))
    rid=create_run(repo,{'workspace_id':w,'start':'2026-01-01T00:00:00+00:00'})
    draft=dict(pattern_key='old',dimension='goals_values',kind='background',title='旧版本',observation='旧版本不在选择范围。',context='test',alternatives=[],question='适用吗？',evidence=[dict(message_id=m['id'],version=1,quote='我去年先规划。',relation='support')])
    execute_run(repo,rid,FixedProvider(draft))
    assert list_insights(repo,w)==[]


def test_undated_message_cannot_become_period_change(db):
    repo,w,draft=prepared(db);draft['kind']='period_change'
    assert not save_insight(repo,'run',draft)['accepted']


def test_model_summary_cannot_bypass_rejected_evidence(db):
    repo,w,draft=prepared(db);rid=create_run(repo,{'workspace_id':w})
    class MaliciousReview:
        calls=0
        def complete_json(self,messages,schema):
            self.calls+=1
            if self.calls==1:return {'insights':[draft]}
            bad=dict(draft,evidence=[dict(draft['evidence'][0],quote='伪造')])
            return {'insights':[bad],'summary':'虚构的秘密经历，不能展示'}
    execute_run(repo,rid,MaliciousReview())
    run=get_run(repo,rid)
    assert run['result']['accepted']==0
    assert '虚构的秘密经历' not in encoded(run)
    assert run['result']['insights']==[]


def test_renamed_rejection_requires_explicit_reinspection(db):
    repo,w,draft=prepared(db)
    first=save_insight(repo,'run',draft)
    revise_insight(repo,w,first['id'],'rejected','不符合','',0)
    save_insight(repo,'run',dict(draft,pattern_key='new-key',title='另一个标题'))
    assert list_insights(repo,w)==[]
    assert len(list_insights(repo,w,include_rejected=True))>=1


def test_snapshot_contains_immutable_validated_findings_and_revisions(db):
    repo,w,draft=prepared(db);rid=create_run(repo,{'workspace_id':w})
    execute_run(repo,rid,FixedProvider(draft))
    item=list_insights(repo,w)[0]
    revise_insight(repo,w,item['id'],'partial','这只适用于两个项目','不能推广',0)
    sid=save_snapshot(repo,w,rid)
    with db.transaction() as c:
        snapshot=json.loads(c.execute('SELECT content FROM profile_snapshots WHERE id=?',(sid,)).fetchone()[0])
    assert snapshot['insights'][0]['evidence'][0]['quote']=='我喜欢先做小版本。'
    assert snapshot['insights'][0]['history'][0]['reason']=='不能推广'


def test_markdown_complete_export_includes_revision_reason(db):
    repo,w,draft=prepared(db);item=save_insight(repo,'run',draft)
    revise_insight(repo,w,item['id'],'partial','我的修订','理由需要保留',0)
    assert '理由需要保留' in export_profile(repo,w,'markdown').decode()


def test_live_job_is_discoverable_and_duplicate_start_is_blocked(tmp_path):
    from test_api import connected
    client,app=connected(tmp_path)
    with client:
        w=client.post('/api/workspaces',json={'name':'w'}).json()['id']
        rid=create_run(app.state.repo,{'workspace_id':w})
        response=client.get('/api/runs',params={'workspace_id':w})
        assert response.status_code==200
        assert response.json()[0]['id']==rid
        with pytest.raises(AppError):create_run(app.state.repo,{'workspace_id':w})


def test_review_covers_late_candidates_and_both_periods(db,monkeypatch):
    import selfdiff.analysis.pipeline as pipeline
    monkeypatch.setattr(pipeline,'MAX_CHARS',6000)
    repo=Repository(db);w=repo.create_workspace('w')['id']
    for index in range(15):
        text=('我在早期选择了规划。' if index<14 else '我在后期选择了验证。')+' 记录'+str(index)+'。'+'材料'*150
        repo.import_preview(w,preview_upload('normalized',str(index)+'.json',sample(text,cid=str(index),timestamp='2026-01-05T00:00:00Z' if index<14 else '2026-09-05T00:00:00Z')))
    scope={'workspace_id':w,'period_a':{'start':'2026-01-01T00:00:00+00:00','end':'2026-02-01T00:00:00+00:00'},'period_b':{'start':'2026-09-01T00:00:00+00:00','end':'2026-10-01T00:00:00+00:00'}}
    class Capture:
        reviewed=set()
        balanced=True
        def complete_json(self,messages,schema):
            body=json.loads(messages[-1]['content']);material=body['untrusted_material']
            if body['phase']=='review':
                self.reviewed.update(c['pattern_key'] for c in body['candidate_insights'])
                self.balanced &= {m['period'] for m in material}=={'A','B'}
                return {'insights':[]}
            return {'insights':[dict(pattern_key=m['id'],dimension='change',kind='period_change',title='待复核',observation='待核对两侧',context='test',alternatives=[],question='有改变吗？',evidence=[dict(message_id=m['id'],version=m['version'],quote=m['text'],relation='support')]) for m in material]}
    provider=Capture();rid=create_run(repo,scope,'comparison');execute_run(repo,rid,provider)
    assert len(provider.reviewed)==15
    assert provider.balanced
