import json
from selfdiff.analysis.jobs import create_run, get_run
from selfdiff.sources.common import timestamp
from selfdiff.errors import AppError
from selfdiff.store.repository import uid, encoded
from selfdiff.insights import list_insights


def challenge(repo, scope, claim):
    if not claim.strip() or len(claim) > 1500:
        raise AppError('claim', '请输入 1–1500 字的具体自我判断。')
    return create_run(repo, dict(scope, claim=claim), 'challenge')


def _period(period):
    start, end = timestamp(period.get('start')), timestamp(period.get('end'))
    if not start or not end or start >= end:
        raise AppError('period', '请选择有效的开始与结束时间，开始须早于结束。')
    return {'start': start, 'end': end}


def compare_periods(repo, scope, a, b, theme):
    if len(theme) > 500:
        raise AppError('theme', '比较主题过长。')
    return create_run(repo, dict(scope, period_a=_period(a), period_b=_period(b), theme=theme), 'comparison')


def save_snapshot(repo, wid, run_id):
    run = get_run(repo, run_id, wid)
    if run['status'] not in ('succeeded', 'partial', 'insufficient'):
        raise AppError('snapshot', '任务未结束，暂不能保存快照。', 409)
    sid = uid()
    frozen = (run['result'] or {}).get('insights', [])
    current_insights = {i['id']: i for i in list_insights(repo, wid, include_rejected=True) if i['run_id'] == run_id}
    findings = [current_insights.get(i['id'], i) for i in frozen]
    with repo.db.transaction() as c:
        current = c.execute('SELECT data_version FROM workspaces WHERE id=?', (wid,)).fetchone()[0]
        if current != run['data_version']:
            raise AppError('stale', '资料已更新或删除，请重新分析后保存。', 409)
        c.execute('INSERT INTO profile_snapshots(id,workspace_id,run_id,content) VALUES(?,?,?,?)',
                  (sid, wid, run_id, encoded({'scope': run['scope'], 'result': run['result'], 'insights': findings, 'analyzed_at': run['created_at'], 'data_version': current})))
    return sid


def list_snapshots(repo, wid):
    with repo.db.transaction() as c:
        return [dict(id=r['id'], created_at=r['created_at'], invalidated=bool(r['invalidated']), **json.loads(r['content']))
                for r in c.execute('SELECT * FROM profile_snapshots WHERE workspace_id=? ORDER BY created_at DESC', (wid,))]
