import json
from selfdiff.errors import AppError
from selfdiff.store.repository import uid, encoded


def create_run(repo, scope, mode='profile'):
    workspace = repo.workspace(scope['workspace_id'])
    rid = uid()
    with repo.db.transaction() as c:
        if c.execute("SELECT 1 FROM analysis_runs WHERE workspace_id=? AND status IN ('queued','running')", (workspace['id'],)).fetchone():
            raise AppError('run_active', '此资料空间已有分析任务，请等待完成或先取消。', 409)
        c.execute('INSERT INTO analysis_runs(id,workspace_id,mode,status,data_version,scope) VALUES(?,?,?,?,?,?)',
                  (rid, workspace['id'], mode, 'queued', workspace['data_version'], encoded(scope)))
    return rid


def get_run(repo, rid, wid=None):
    with repo.db.transaction() as c:
        row = c.execute('SELECT * FROM analysis_runs WHERE id=?', (rid,)).fetchone()
    if not row or (wid and row['workspace_id'] != wid):
        raise AppError('not_found', '分析任务不存在。', 404)
    result = dict(row)
    result['scope'] = json.loads(result['scope'])
    result['result'] = json.loads(result['result']) if result['result'] else None
    return result


def list_runs(repo, wid):
    repo.workspace(wid)
    with repo.db.transaction() as c:
        ids = [r[0] for r in c.execute('SELECT id FROM analysis_runs WHERE workspace_id=? ORDER BY rowid DESC LIMIT 20', (wid,))]
    return [get_run(repo, rid, wid) for rid in ids]


def cancel_run(repo, rid):
    with repo.db.transaction() as c:
        c.execute("UPDATE analysis_runs SET status='cancelled' WHERE id=? AND status IN ('queued','running')", (rid,))


def interrupt_runs(repo):
    with repo.db.transaction() as c:
        c.execute("UPDATE analysis_runs SET status='interrupted' WHERE status IN ('queued','running')")
