from selfdiff.demo import create_demo_workspace
from selfdiff.store.repository import Repository
from selfdiff.insights import list_insights
from selfdiff.evidence import validate_evidence
from selfdiff.exports import export_profile


def test_demo_has_cited_six_dimensions_without_personal_leakage(db):
    repo=Repository(db)
    personal=repo.create_workspace('我的资料')['id']
    demo=create_demo_workspace(repo)
    assert demo != personal
    assert repo.workspace(demo)['demo']
    assert len(repo.conversations(demo))==12
    assert len({c['source'] for c in repo.conversations(demo)})==3
    insights=list_insights(repo,demo)
    assert len({i['dimension'] for i in insights})==6
    for insight in insights:
        refs=[{k:e[k] for k in ('message_id','version','quote','relation')} for e in insight['evidence']]
        assert validate_evidence(repo,demo,refs)['valid']
    assert '我总想把方案'.encode() not in export_profile(repo,personal,'json')
    assert repo.messages(personal)==[]


def test_demo_api_comparison_works_without_key(tmp_path):
    from test_api import connected
    client,app=connected(tmp_path)
    with client:
        response=client.post('/api/demo')
        assert response.status_code==200
        wid=response.json()['id']
        result=client.post('/api/comparisons',json={'scope':{'workspace_id':wid},'theme':'项目启动方式','period_a':{'start':'2026-01-01T00:00:00Z','end':'2026-02-01T00:00:00Z'},'period_b':{'start':'2026-09-01T00:00:00Z','end':'2026-10-01T00:00:00Z'}})
        assert result.status_code==200
        run=client.get('/api/runs/'+result.json()['id'],params={'workspace_id':wid}).json()
        assert run['status']=='succeeded' and run['result']['demo']


def test_demo_rejects_personal_imports(tmp_path):
    from test_api import connected
    from test_repository import sample
    client,app=connected(tmp_path)
    with client:
        wid=client.post('/api/demo').json()['id']
        response=client.post('/api/imports/preview',params={'workspace_id':wid,'source':'normalized','filename':'mine.json'},content=sample())
        assert response.status_code==409
