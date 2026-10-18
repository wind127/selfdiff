import json
import re
import unicodedata
from pydantic import ValidationError
from selfdiff.models import InsightDraft
from selfdiff.evidence import validate_evidence
from selfdiff.errors import AppError
from selfdiff.store.repository import uid, encoded


def save_insight(repo, run_id, draft):
    try:
        draft = draft if isinstance(draft, InsightDraft) else InsightDraft.model_validate(draft)
    except ValidationError:
        return {'accepted': False, 'reason': 'invalid_schema'}
    with repo.db.transaction() as c:
        run = c.execute('SELECT * FROM analysis_runs WHERE id=?', (run_id,)).fetchone()
    if not run:
        return {'accepted': False, 'reason': 'missing_run'}
    wid = run['workspace_id']
    checked = validate_evidence(repo, wid, draft.evidence)
    if not checked['valid']:
        return {'accepted': False, 'reason': 'invalid_evidence'}
    scope = json.loads(run['scope'])
    for ref in draft.evidence:
        message = repo.message(wid, ref.message_id, ref.version)
        time = message['occurred_at']
        if not message['active'] or message['active_version'] != ref.version:
            return {'accepted': False, 'reason': 'outside_current_version'}
        if scope.get('source_ids') and message['source'] not in scope['source_ids']:
            return {'accepted': False, 'reason': 'outside_scope'}
        if (scope.get('start') and (not time or time < scope['start'])) or (scope.get('end') and (not time or time >= scope['end'])):
            return {'accepted': False, 'reason': 'outside_scope'}
        if run['mode'] == 'comparison' and not any(time and p['start'] <= time < p['end'] for p in (scope['period_a'], scope['period_b'])):
            return {'accepted': False, 'reason': 'outside_periods'}
    supports = [r for r in checked['records'] if r['relation'] == 'support']
    independent = {r['independent_id'] for r in supports}
    if not supports or (draft.kind in ('recurring_blocker', 'success_condition') and len(independent) < 2):
        return {'accepted': False, 'reason': 'insufficient_independent_evidence'}
    if draft.kind == 'background' and any(repo.message(wid, r['message_id'], r['version'])['content_kind'] != 'self_report' for r in supports):
        return {'accepted': False, 'reason': 'not_explicit_self_report'}
    if draft.kind == 'period_change' or run['mode'] == 'comparison':
        dates = {r['occurred_at'] for r in supports if r['occurred_at']}
        if len(dates) < 2:
            return {'accepted': False, 'reason': 'insufficient_time_evidence'}
        if run['mode'] == 'comparison' and not all(any(p['start'] <= date < p['end'] for date in dates) for p in (scope['period_a'], scope['period_b'])):
            return {'accepted': False, 'reason': 'missing_period_evidence'}
    key = unicodedata.normalize('NFKC', draft.pattern_key).casefold().strip()
    key = re.sub(r'\s+', '-', key)
    content = draft.model_dump()
    content['independent_conversations'] = len(independent)
    dates = [r['occurred_at'] for r in checked['records'] if r['occurred_at']]
    content['time_range'] = [min(dates), max(dates)] if dates else None
    content['coverage'] = {'run_id': run_id, 'analyzed_at': run['created_at']}
    with repo.db.transaction() as c:
        current = c.execute('SELECT data_version FROM workspaces WHERE id=?', (wid,)).fetchone()
        state = c.execute('SELECT status FROM analysis_runs WHERE id=?', (run_id,)).fetchone()
        if current['data_version'] != run['data_version'] or state['status'] not in ('running', 'succeeded', 'partial'):
            return {'accepted': False, 'reason': 'stale_or_cancelled'}
        old = c.execute('SELECT id,status,invalidated FROM insights WHERE workspace_id=? AND pattern_key=?', (wid, key)).fetchone()
        if old and old['status'] in ('rejected', 'confirmed', 'partial'):
            return {'accepted': False, 'reason': 'preserve_user_review'}
        # Semantic identity cannot be reliably established from a model's key. After a rejection,
        # quarantine fresh model claims until the person explicitly reviews them.
        quarantine = bool(c.execute("SELECT 1 FROM insights WHERE workspace_id=? AND status='rejected' LIMIT 1", (wid,)).fetchone())
        status = 'review_required' if quarantine else 'pending'
        iid = old['id'] if old else uid()
        if old:
            c.execute('UPDATE insights SET content=?,run_id=?,invalidated=0,status=? WHERE id=?', (encoded(content), run_id, status, iid))
            c.execute('DELETE FROM evidence WHERE insight_id=?', (iid,))
        else:
            c.execute('INSERT INTO insights(id,workspace_id,run_id,pattern_key,dimension,kind,content,status) VALUES(?,?,?,?,?,?,?,?)', (iid, wid, run_id, key, draft.dimension, draft.kind, encoded(content), status))
        for ref in draft.evidence:
            c.execute('INSERT INTO evidence(id,insight_id,workspace_id,message_id,version,quote,relation) VALUES(?,?,?,?,?,?,?)', (uid(), iid, wid, ref.message_id, ref.version, ref.quote, ref.relation))
    return {'accepted': not quarantine, 'id': iid, 'reason': 'explicit_review_required' if quarantine else None}


def list_insights(repo, wid, include_rejected=False):
    repo.workspace(wid)
    with repo.db.transaction() as c:
        rows = c.execute('SELECT * FROM insights WHERE workspace_id=? AND invalidated=0 ORDER BY rowid DESC', (wid,)).fetchall()
        result = []
        for r in rows:
            if r['status'] in ('rejected', 'review_required') and not include_rejected:
                continue
            data = dict(json.loads(r['content']), id=r['id'], run_id=r['run_id'], status=r['status'], revision=r['revision'])
            data['evidence'] = [dict(e) for e in c.execute('SELECT e.message_id,e.version,e.quote,e.relation,v.occurred_at,m.conversation_id,c.title,c.source FROM evidence e JOIN messages m ON m.id=e.message_id JOIN message_versions v ON v.message_id=e.message_id AND v.version=e.version JOIN conversations c ON c.id=m.conversation_id WHERE e.insight_id=?', (r['id'],))]
            data['history'] = [dict(h) for h in c.execute('SELECT version,verdict,text,reason,origin,created_at FROM insight_revisions WHERE insight_id=? ORDER BY version', (r['id'],))]
            data['user_text'] = data['history'][-1]['text'] if data['history'] else ''
            result.append(data)
        return result


def revise_insight(repo, wid, iid, verdict, text, reason, expected_revision):
    if verdict not in ('confirmed', 'partial', 'rejected', 'reopen') or len(text) > 4000 or len(reason) > 2000:
        raise AppError('revision', '修订内容或状态无效。')
    with repo.db.transaction() as c:
        row = c.execute('SELECT * FROM insights WHERE workspace_id=? AND id=? AND invalidated=0', (wid, iid)).fetchone()
        if not row:
            raise AppError('not_found', '洞察不存在或来源已删除。', 404)
        if row['revision'] != expected_revision:
            raise AppError('conflict', '洞察已有新修订，请刷新后重试。', 409)
        version = row['revision']+1
        c.execute('INSERT INTO insight_revisions(id,insight_id,version,verdict,text,reason) VALUES(?,?,?,?,?,?)', (uid(), iid, version, verdict, text, reason))
        c.execute('UPDATE insights SET status=?,revision=? WHERE id=?', ('pending' if verdict == 'reopen' else verdict, version, iid))
    return {'version': version, 'verdict': verdict, 'text': text, 'reason': reason, 'origin': 'user_revision'}
