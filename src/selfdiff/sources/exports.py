import json
from selfdiff.models import ConversationInput, ParseResult
from selfdiff.errors import AppError
from .common import message


def parse(source, filename, text):
    items = json.loads(text)
    if not isinstance(items, list):
        raise AppError('format', '请选择官方 conversations.json 导出文件。')
    conversations = []
    for item in items:
        msgs = []
        if source == 'chatgpt':
            mapping, cursor, visited = item.get('mapping', {}), item.get('current_node'), set()
            if not cursor:
                continue
            chain = []
            while cursor and cursor in mapping:
                if cursor in visited:
                    raise AppError('format', '会话分支包含循环。')
                visited.add(cursor)
                node = mapping[cursor]
                chain.append((cursor, node.get('message') or {}))
                cursor = node.get('parent')
            for mid, m in reversed(chain):
                content = m.get('content') or {}
                part = content.get('parts', []) if content.get('content_type', 'text') == 'text' else []
                msg = message(mid, (m.get('author') or {}).get('role'), part, m.get('create_time'))
                if msg:
                    msgs.append(msg)
        else:
            for i, m in enumerate(item.get('chat_messages', [])):
                msg = message(m.get('uuid', i), m.get('sender'), m.get('text') or m.get('content'), m.get('created_at'))
                if msg:
                    msgs.append(msg)
        if msgs:
            conversations.append(ConversationInput(external_id=str(item.get('id') or item.get('uuid')), title=item.get('title') or item.get('name') or source, source=source, messages=msgs, complete_snapshot=True))
    return ParseResult(conversations=conversations, warnings=[] if conversations else ['未找到受支持的导出会话。'])
