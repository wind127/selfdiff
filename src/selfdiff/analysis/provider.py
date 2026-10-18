import json
import os
from urllib.parse import urlsplit
import httpx
from selfdiff.errors import AppError


class Provider:
    def __init__(self, base_url, model, key=None, transport=None):
        parts = urlsplit(base_url)
        if (parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password
                or parts.query or parts.fragment or (parts.scheme == 'http' and parts.hostname not in ('localhost', '127.0.0.1', '::1'))):
            raise AppError('provider_url', '模型地址需为 HTTPS 或本机 HTTP，且不能包含凭据或查询参数。')
        if not model.strip():
            raise AppError('provider_model', '请填写模型名称。')
        self.base_url, self.model = base_url.rstrip('/'), model.strip()
        self.key = key if key is not None else os.environ.get('SELFDIFF_API_KEY', '')
        self.transport = transport

    def complete_json(self, messages, schema):
        headers = {'Authorization': 'Bearer '+self.key} if self.key else {}
        chat = list(messages)
        with httpx.Client(timeout=httpx.Timeout(90, connect=15), transport=self.transport, follow_redirects=False) as client:
            for attempt in range(2):
                try:
                    response = client.post(self.base_url+'/chat/completions', headers=headers,
                                           json={'model': self.model, 'messages': chat, 'temperature': 0.2,
                                                 'max_tokens': 6000, 'response_format': {'type': 'json_object'}})
                    response.raise_for_status()
                    if len(response.content) > 2_000_000:
                        raise AppError('provider_size', '模型响应过大，未保存。')
                    text = response.json()['choices'][0]['message']['content']
                    result = json.loads(text)
                    if not isinstance(result, dict) or any(k not in result for k in schema.get('required', [])):
                        raise ValueError('schema')
                    return result
                except (httpx.HTTPError, httpx.InvalidURL):
                    raise AppError('provider_unavailable', '模型连接失败或请求被拒绝；请检查地址、模型、额度和进程环境中的密钥。', 502) from None
                except (ValueError, KeyError, IndexError, TypeError):
                    if attempt:
                        raise AppError('provider_format', '模型两次返回的格式均无法读取；原始资料保持完整。', 502) from None
                    # Never echo a failed provider response back into context/logs.
                    chat = list(messages)+[{'role': 'user', 'content': 'Return only valid JSON matching this schema: '+json.dumps(schema)}]

    def test_connection(self):
        self.complete_json([{'role': 'user', 'content': 'Return a JSON object with ok=true. No personal material is included.'}], {'type': 'object'})
        return {'connected': True, 'model': self.model}
