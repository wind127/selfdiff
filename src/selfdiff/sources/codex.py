import json
from pathlib import Path
from selfdiff.models import ConversationInput, ParseResult
from .common import message


def parse(filename, text):
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    meta = next((r.get('payload', {}) for r in rows if r.get('type') == 'session_meta'), {})
    sid = str(meta.get('id', Path(filename).stem))
    canonical = any(r.get('type') == 'response_item' and r.get('payload', {}).get('type') == 'message' for r in rows)
    msgs = []
    for i, row in enumerate(rows):
        p = row.get('payload', {})
        m = None
        if row.get('type') == 'response_item' and p.get('type') == 'message':
            m = message(p.get('id', i), p.get('role'), p.get('content'), row.get('timestamp'))
        elif not canonical and row.get('type') == 'event_msg' and p.get('type') in ('user_message', 'agent_message'):
            m = message(p.get('id', i), 'user' if p['type'] == 'user_message' else 'assistant', p.get('message'), row.get('timestamp'))
        if m:
            msgs.append(m)
    return ParseResult(conversations=[ConversationInput(external_id=sid, title=f'Codex · {sid[:8]}', source='codex', messages=msgs, branch_id=meta.get('forked_from_id'))] if msgs else [], warnings=[] if msgs else ['未识别到 Codex 文本消息。'])
