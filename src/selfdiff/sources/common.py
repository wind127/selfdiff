from datetime import datetime, timezone
import re
from selfdiff.models import MessageInput


def timestamp(value):
    try:
        if isinstance(value, (float, int)):
            dt = datetime.fromtimestamp(value, timezone.utc)
        elif isinstance(value, str) and value:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                return None
        else:
            return None
        return dt.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def text_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(text_content(x) for x in content if isinstance(x, (str, dict)))
    if isinstance(content, dict):
        if content.get('type') in ('tool_result', 'tool_use', 'image', 'image_url'):
            return ''
        return str(content.get('text', ''))
    return ''


def message(mid, role, content, time=None, parent=None):
    text = text_content(content).strip()
    if not text:
        return None
    role = {'human': 'user', 'gpt': 'assistant'}.get(role, role)
    if role not in ('user', 'assistant', 'system', 'tool'):
        role = 'unknown'
    kind = 'uncertain'
    if role != 'user':
        kind = 'tool' if role == 'tool' else 'assistant'
    elif re.search(r'```|^>|<environment_context>|<user_instructions>|<system|<developer|AGENTS\.md', text, re.M):
        kind = 'quoted'
    elif re.search(r'假设|如果我是|扮演|role.?play|pretend', text, re.I):
        kind = 'hypothetical'
    elif re.search(r'[？?]', text):
        kind = 'question'
    elif re.match(r'(我|最近我|今天我|I\b|My\b)', text, re.I):
        kind = 'self_report'
    return MessageInput(external_id=str(mid), role=role, text=text, occurred_at=timestamp(time), content_kind=kind, parent_id=parent)
