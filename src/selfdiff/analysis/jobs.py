import json
from selfdiff.errors import AppError
from selfdiff.store.repository import uid, encoded


def create_run(repo, scope, mode='profile'):
    workspace = repo.workspace(scope['workspace_id'])
    rid = uid()
    with repo.db.transaction() as c:
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


def cancel_run(repo, rid):
    with repo.db.transaction() as c:
        c.execute("UPDATE analysis_runs SET status='cancelled' WHERE id=? AND status IN ('queued','running')", (rid,))


def interrupt_runs(repo):
    with repo.db.transaction() as c:
        c.execute("UPDATE analysis_runs SET status='interrupted' WHERE status IN ('queued','running')")
