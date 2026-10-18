import json
from pydantic import ValidationError
from selfdiff.errors import AppError
from . import normalized, codex, claude_code, workbuddy, exports

SOURCES = ['normalized', 'codex', 'claude-code', 'workbuddy', 'chatgpt', 'claude-web']


def parse_bytes(source, filename, data):
    if source not in SOURCES:
        raise AppError('source', '不支持的来源；可转换为标准 JSON 或带角色的文本。')
    try:
        text = data.decode('utf-8-sig')
        if source in ('chatgpt', 'claude-web'):
            return exports.parse(source, filename, text)
        return {'normalized': normalized, 'codex': codex, 'claude-code': claude_code, 'workbuddy': workbuddy}[source].parse(filename, text)
    except (UnicodeError, json.JSONDecodeError, ValidationError, TypeError, ValueError, AttributeError, KeyError, RecursionError):
        raise AppError('format', '内容不符合所选来源的 UTF-8 会话格式；请检查导出文件或使用标准格式。') from None
