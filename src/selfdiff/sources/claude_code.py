import json
from pathlib import Path
from selfdiff.models import ConversationInput, ParseResult
from .common import message


def parse(filename, text, source='claude-code'):
    groups = {}
    seen = set()
    for i, line in enumerate(text.splitlines()):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get('type') not in ('user', 'assistant', 'message') or row.get('isMeta') or row.get('isCompactSummary'):
            continue
        p = row.get('message', row)
        mid = str(row.get('uuid', row.get('id', i)))
        sid = str(row.get('sessionId', row.get('session_id', Path(filename).stem)))
        if (sid, mid) in seen:
            continue
        m = message(mid, p.get('role', row.get('type')), p.get('content'), row.get('timestamp'), row.get('parentUuid'))
        if m:
            seen.add((sid, mid))
            groups.setdefault(sid, []).append(m)
    return ParseResult(conversations=[ConversationInput(external_id=sid, title=f'{source} · {sid[:8]}', source=source, messages=msgs) for sid, msgs in groups.items()], warnings=[] if groups else ['未识别到文本消息；未知记录未纳入。'])
