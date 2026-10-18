import json
import re
from pathlib import Path
from selfdiff.models import ConversationInput, ParseResult
from .common import message


def parse(filename, text):
    if Path(filename).suffix.lower() in ('.json', '.jsonl'):
        data = json.loads(text)
        items = data.get('conversations', [data]) if isinstance(data, dict) else data
    else:
        chunks = re.split(r'(?m)^\s*(?:#{1,3}\s*)?(User|Assistant|用户|助手):\s*', text)
        if len(chunks) < 3:
            return ParseResult(warnings=['缺少 User:/Assistant: 发言标记，资料未参与分析。'], unsupported_count=1)
        items = [{'id': Path(filename).stem, 'title': Path(filename).stem, 'messages': [
            {'id': str(i), 'role': {'用户': 'user', '助手': 'assistant'}.get(chunks[i], chunks[i].lower()), 'content': chunks[i+1]}
            for i in range(1, len(chunks)-1, 2)]}]
    result = ParseResult()
    for i, item in enumerate(items):
        msgs = [message(m.get('id', j), m.get('role', 'unknown'), m.get('content', m.get('text', '')), m.get('timestamp'), m.get('parent_id')) for j, m in enumerate(item.get('messages', []))]
        msgs = [m for m in msgs if m]
        if msgs:
            result.conversations.append(ConversationInput(external_id=str(item.get('id', f'{Path(filename).stem}:{i}')), title=item.get('title') or Path(filename).stem, source='normalized', messages=msgs, branch_id=item.get('branch_id')))
    if not result.conversations:
        result.warnings.append('未找到可识别的会话。')
    return result
