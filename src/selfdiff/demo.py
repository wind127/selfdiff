from importlib.resources import files
import json
from selfdiff.sources.ingest import preview_upload
from selfdiff.insights import save_insight, list_insights
from selfdiff.analysis.jobs import create_run, get_run
from selfdiff.store.repository import encoded
from selfdiff.errors import AppError


def create_demo_workspace(repo):
    wid = repo.create_workspace('小林的研究档案 · 合成示例', demo=True)['id']
    story = json.loads(files('selfdiff').joinpath('data/demo.json').read_text(encoding='utf-8'))
    conversations = []
    for i, item in enumerate(story):
        for phase, month in [('a', '01'), ('b', '09')]:
            conversations.append({'id':f'demo-{i}-{phase}', 'title':['项目取舍','方案比较','学习与协作','一日交付','兴趣主线','启动方法'][i],
                                  'messages':[{'id':'user', 'role':'user', 'content':item[phase], 'timestamp':f'2026-{month}-{i+3:02d}T09:00:00Z'},
                                              {'id':'assistant','role':'assistant','content':'我们可以从这次具体的选择开始梳理。'}]})
    preview = preview_upload('normalized', 'demo.json', encoded({'conversations':conversations}).encode())
    for i, conversation in enumerate(preview.conversations):
        conversation.source = ['codex','claude-code','workbuddy'][i % 3]
    repo.import_preview(wid, preview, allow_demo_seed=True)
    rid = create_run(repo, {'workspace_id':wid})
    with repo.db.transaction() as c:
        c.execute("UPDATE analysis_runs SET status='running',total_batches=1,completed_batches=1 WHERE id=?", (rid,))
    messages = repo.messages(wid)
    for i, item in enumerate(story):
        refs = [{'message_id':m['id'],'version':m['version'],'quote':m['text'],'relation':'support'} for m in messages if m['text'] in (item['a'],item['b'])]
        draft = dict(pattern_key='demo-'+item['dimension'], dimension=item['dimension'], kind=item['kind'], title=item['title'],
                     observation=item['observation'], context=item['context'], alternatives=[item['alternative']], question=item['question'], evidence=refs)
        outcome = save_insight(repo, rid, draft)
        if not outcome['accepted']:
            raise RuntimeError('Synthetic demo evidence failed validation')
    findings = list_insights(repo, wid)
    with repo.db.transaction() as c:
        c.execute("UPDATE analysis_runs SET status='succeeded',result=? WHERE id=?", (encoded({'demo':True,'accepted':6,'insights':findings,'summary':'预创作的合成示例；没有调用模型。'}),rid))
    return wid


def demo_run(repo, scope, mode):
    if mode == 'challenge' and scope.get('claim') != '我是不是经常换方向':
        raise AppError('demo_claim', '示例只演示预设判断；请在自己的资料空间分析其他问题。')
    rid = create_run(repo, scope, mode)
    summary = ('表面上你更换了几次工具形式，但持续围绕“让零散材料再次产生价值”。换形式和换目标需要区分。'
               if mode == 'challenge' else '一月倾向先完成整体规划，九月倾向先验证一个场景。项目阶段不同也是合理解释，需本人确认。')
    findings = [i for i in list_insights(repo, scope['workspace_id']) if i['dimension'] in (['interests','thinking_decisions'] if mode == 'challenge' else ['change'])]
    with repo.db.transaction() as c:
        c.execute("UPDATE analysis_runs SET status='succeeded',total_batches=1,completed_batches=1,result=? WHERE id=?", (encoded({'demo':True,'summary':summary,'insights':findings,'classification':'uncertain','note':'这是预设情境的合成演示，没有分析真实用户，也未调用模型。'}),rid))
    return rid
