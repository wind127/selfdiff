import json
import pytest
from selfdiff.sources.registry import parse_bytes
from selfdiff.errors import AppError


def parsed(source, rows):
    text = '\n'.join(json.dumps(r, ensure_ascii=False) for r in rows)
    return parse_bytes(source, '会话.jsonl', text.encode())


def test_normalized_json_and_unknown_time():
    data = {'conversations': [{'id': 'c', 'title': '工作', 'messages': [
        {'id': 'u', 'role': 'user', 'content': '我想先做一个小版本。'},
        {'id': 'a', 'role': 'assistant', 'content': '先验证需求。'}]}]}
    result = parse_bytes('normalized', '输入.json', b'\xef\xbb\xbf'+json.dumps(data).encode())
    assert result.conversations[0].messages[0].text == '我想先做一个小版本。'
    assert result.conversations[0].messages[0].occurred_at is None


def test_text_requires_explicit_speakers():
    result = parse_bytes('normalized', 'one.md', 'User: 我需要一个计划\nAssistant: 可以先做一步'.encode())
    assert [m.role for m in result.conversations[0].messages] == ['user', 'assistant']
    result = parse_bytes('normalized', 'unknown.txt', '这是没有角色标记的资料'.encode())
    assert result.conversations == [] and result.warnings


def test_codex_does_not_double_count_event_and_response():
    result = parsed('codex', [
        {'type': 'session_meta', 'payload': {'id': 's1'}},
        {'type': 'event_msg', 'payload': {'type': 'user_message', 'message': '我希望逐步验证。'}},
        {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': [{'type': 'input_text', 'text': '我希望逐步验证。'}]}},
        {'type': 'response_item', 'payload': {'type': 'function_call_output', 'output': 'private tool'}}])
    assert [m.text for m in result.conversations[0].messages] == ['我希望逐步验证。']


@pytest.mark.parametrize('source', ['claude-code', 'workbuddy'])
def test_nested_text_and_tools_do_not_become_self_report(source):
    result = parsed(source, [
        {'type': 'user' if source == 'claude-code' else 'message', 'uuid': 'u', 'sessionId': 's', 'message': {'role': 'user', 'content': [{'type': 'text', 'text': '我喜欢写小工具。'}]}},
        {'type': 'user' if source == 'claude-code' else 'message', 'uuid': 't', 'sessionId': 's', 'message': {'role': 'user', 'content': [{'type': 'tool_result', 'content': 'shell output'}]}}])
    assert result.conversations[0].messages[0].text == '我喜欢写小工具。'
    assert len(result.conversations[0].messages) == 1


def test_chatgpt_uses_selected_branch():
    def node(parent, role, text):
        return {'parent': parent, 'message': {'author': {'role': role}, 'content': {'parts': [text]}}}
    data = [{'id': 'c', 'title': 't', 'current_node': 'selected', 'mapping': {
        'root': node(None, 'system', ''), 'u': node('root', 'user', '我选择先验证'),
        'other': node('u', 'assistant', '分支不要导入'), 'selected': node('u', 'assistant', '所选分支')}}]
    result = parse_bytes('chatgpt', 'conversations.json', json.dumps(data).encode())
    assert [m.text for m in result.conversations[0].messages] == ['我选择先验证', '所选分支']


def test_claude_web_export():
    data = [{'uuid': 'c', 'name': 't', 'chat_messages': [
        {'uuid': 'u', 'sender': 'human', 'text': '我在学数据库', 'created_at': '2026-01-01T00:00:00Z'}]}]
    result = parse_bytes('claude-web', 'conversations.json', json.dumps(data).encode())
    assert result.conversations[0].messages[0].role == 'user'
    assert result.conversations[0].messages[0].occurred_at.startswith('2026-01-01')


def test_unknown_source_and_bad_encoding_are_readable_errors():
    for source, data in [('unknown', b'{}'), ('normalized', b'\xff')]:
        with pytest.raises(AppError):
            parse_bytes(source, 'x.json', data)
