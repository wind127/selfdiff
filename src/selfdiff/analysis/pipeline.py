from hashlib import sha256
import json
from selfdiff.errors import AppError
from selfdiff.models import InsightDraft
from selfdiff.evidence import validate_evidence
from selfdiff.insights import save_insight
from selfdiff.store.repository import encoded, uid
from .jobs import get_run
from .prompts import prompt, SCHEMA

MAX_CHARS = 24000
MAX_MESSAGES = 40


def material_for(repo, scope):
    return [dict(id=m['id'], version=m['version'], conversation_id=m['conversation_id'], source=m['source'],
                 text=m['text'], occurred_at=m['occurred_at'], content_kind=m['content_kind'])
            for m in repo.messages(scope['workspace_id'], limit=100000, scope=scope)
            if m['role'] == 'user' and m['content_kind'] not in ('quoted', 'hypothetical', 'tool')]


def chunks(messages):
    current, count = [], 0
    for m in messages:
        for start in range(0, len(m['text']), 8000):
            part = dict(m, text=m['text'][start:start+8000])
            size = len(encoded(part))
            if current and (count+size > MAX_CHARS or len(current) >= MAX_MESSAGES):
                yield current
                current, count = [], 0
            current.append(part)
            count += size
    if current:
        yield current


def prepare_analysis(repo, scope):
    material = material_for(repo, scope)
    return {'message_count': len(material), 'batch_count': len(list(chunks(material))),
            'sources': sorted({m['source'] for m in material}), 'scope': scope,
            'notice': '仅在启动后发送所选用户发言到配置的模型。批次是估算，费用由供应商决定。'}


def _alive(repo, run):
    with repo.db.transaction() as c:
        row = c.execute('SELECT r.status,w.data_version FROM analysis_runs r JOIN workspaces w ON w.id=r.workspace_id WHERE r.id=?', (run['id'],)).fetchone()
        if row['status'] != 'running':
            return False
        if row['data_version'] != run['data_version']:
            c.execute("UPDATE analysis_runs SET status='interrupted',error='source_updated' WHERE id=?", (run['id'],))
            return False
        return True


def execute_run(repo, rid, provider):
    run = get_run(repo, rid)
    if run['status'] != 'queued':
        return
    with repo.db.transaction() as c:
        c.execute("UPDATE analysis_runs SET status='running' WHERE id=? AND status='queued'", (rid,))
    try:
        scope = run['scope']
        material = material_for(repo, scope)
        if run['mode'] == 'comparison':
            a, b = scope['period_a'], scope['period_b']
            left = material_for(repo, dict(scope, start=a['start'], end=a['end']))
            right = material_for(repo, dict(scope, start=b['start'], end=b['end']))
            material = [dict(m, period='A') for m in left]+[dict(m, period='B') for m in right]
            if not left or not right:
                _finish(repo, rid, 'insufficient', {'summary': '两个时期均需有带时间的用户材料。'})
                return
        batches = list(chunks(material))
        with repo.db.transaction() as c:
            c.execute('UPDATE analysis_runs SET total_batches=? WHERE id=?', (len(batches), rid))
            known = [dict(r) for r in c.execute('SELECT pattern_key,status FROM insights WHERE workspace_id=? AND invalidated=0 LIMIT 100', (run['workspace_id'],))]
        if not batches:
            _finish(repo, rid, 'insufficient', {'summary': '所选范围内没有可分析的用户发言。'})
            return
        candidates, rejected, successes, failures = [], 0, 0, 0
        allowed = {m['id'] for m in material}
        for batch in batches:
            if not _alive(repo, run):
                return
            digest = sha256(encoded([run['mode'], scope, batch, provider.__class__.__name__, getattr(provider, 'model', ''), getattr(provider, 'base_url', '')]).encode()).hexdigest()
            with repo.db.transaction() as c:
                cached = c.execute('SELECT payload FROM analysis_batches WHERE workspace_id=? AND input_hash=? LIMIT 1', (run['workspace_id'], digest)).fetchone()
            try:
                response = json.loads(cached['payload']) if cached else provider.complete_json(prompt('extract', run['mode'], scope, batch, known=known), SCHEMA)
                if not isinstance(response.get('insights'), list):
                    raise AppError('provider_format', '模型未返回可读取的发现列表。')
                if not _alive(repo, run):
                    return
                for raw in response['insights'][:30]:
                    try:
                        draft = InsightDraft.model_validate(raw)
                        checked = validate_evidence(repo, run['workspace_id'], draft.evidence)
                        if not checked['valid'] or any(e.message_id not in allowed for e in draft.evidence):
                            rejected += 1
                        else:
                            candidates.append(draft.model_dump())
                    except ValueError:
                        rejected += 1
                successes += 1
                with repo.db.transaction() as c:
                    # Repeat version/state check inside the transaction to close deletion races.
                    current = c.execute('SELECT data_version FROM workspaces WHERE id=?', (run['workspace_id'],)).fetchone()[0]
                    state = c.execute('SELECT status FROM analysis_runs WHERE id=?', (rid,)).fetchone()[0]
                    if current != run['data_version'] or state != 'running':
                        return
                    if not cached:
                        c.execute('INSERT INTO analysis_batches(id,workspace_id,run_id,input_hash,payload) VALUES(?,?,?,?,?)', (uid(), run['workspace_id'], rid, digest, encoded(response)))
                    c.execute('UPDATE analysis_runs SET completed_batches=?,rejected_candidates=? WHERE id=?', (successes, rejected, rid))
            except AppError:
                failures += 1
        accepted, summary, classification = 0, '当前资料未检索到反例；这不代表现实中不存在。', 'uncertain'
        if candidates and _alive(repo, run):
            # Bounded review retrieves original excerpts from both supporting and other contexts.
            review_material, review_size = [], 0
            for item in material:
                excerpt = dict(item, text=item['text'][:2500])
                size = len(encoded(excerpt))
                if review_size+size > MAX_CHARS:
                    break
                review_material.append(excerpt)
                review_size += size
            try:
                reviewed = provider.complete_json(prompt('review', run['mode'], scope, review_material, candidates[:12], known), SCHEMA)
                summary = str(reviewed.get('summary') or summary)[:3000]
                classification = reviewed.get('classification', 'uncertain')
                for raw in reviewed.get('insights', [])[:30]:
                    if not _alive(repo, run):
                        return
                    refs = raw.get('evidence', []) if isinstance(raw, dict) else []
                    if any(r.get('message_id') not in allowed for r in refs):
                        rejected += 1
                        continue
                    outcome = save_insight(repo, rid, raw)
                    accepted += int(outcome['accepted'])
                    rejected += int(not outcome['accepted'])
            except AppError:
                failures += 1
        if not _alive(repo, run):
            return
        with repo.db.transaction() as c:
            c.execute('UPDATE analysis_runs SET rejected_candidates=? WHERE id=?', (rejected, rid))
        status = 'partial' if failures and successes else ('failed' if failures else 'succeeded')
        _finish(repo, rid, status, {'accepted': accepted, 'summary': summary, 'classification': classification,
                                  'scope': scope, 'note': '待本人确认；材料记录范围不等于现实全部经历。'}, run['data_version'])
    except Exception:
        # Deliberately omit exception text: HTTP errors and malformed data may contain secrets.
        _finish(repo, rid, 'failed', {'summary': '分析未完成；请检查模型配置并重试。'}, run['data_version'])


def _finish(repo, rid, status, result, expected_version=None):
    with repo.db.transaction() as c:
        row = c.execute('SELECT r.status,w.data_version FROM analysis_runs r JOIN workspaces w ON w.id=r.workspace_id WHERE r.id=?', (rid,)).fetchone()
        if row and row['status'] == 'running' and (expected_version is None or row['data_version'] == expected_version):
            c.execute('UPDATE analysis_runs SET status=?,result=? WHERE id=?', (status, encoded(result), rid))
