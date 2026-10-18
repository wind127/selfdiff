import json
import subprocess
import sys
import os
from fastapi.testclient import TestClient
from selfdiff.api.app import create_app
from test_repository import sample


def connected(tmp_path):
    app = create_app(tmp_path, 8765)
    client = TestClient(app, base_url='http://127.0.0.1:8765')
    response = client.post('/api/session/bootstrap', json={'token':app.state.bootstrap})
    assert response.status_code == 200
    client.headers['X-CSRF-Token'] = response.json()['csrf']
    return client,app


def test_api_import_preview_confirm_search_delete(tmp_path):
    client,app=connected(tmp_path)
    with client:
        wid=client.post('/api/workspaces',json={'name':'我的资料'}).json()['id']
        preview=client.post('/api/imports/preview',params={'workspace_id':wid,'source':'normalized','filename':'a.json'},content=sample()).json()
        assert preview['message_count']==1
        assert client.get('/api/conversations',params={'workspace_id':wid}).json()==[]
        response=client.post('/api/imports/'+preview['preview_id']+'/confirm',json={'workspace_id':wid})
        assert response.status_code==200
        messages=client.get('/api/messages',params={'workspace_id':wid,'query':'小版本'}).json()
        assert messages[0]['text']=='我喜欢先做小版本。'
        response=client.delete('/api/conversations/'+messages[0]['conversation_id'],params={'workspace_id':wid})
        assert response.status_code==200
        assert client.get('/api/messages',params={'workspace_id':wid}).json()==[]


def test_local_auth_blocks_foreign_sites_and_missing_token(tmp_path):
    client,app=connected(tmp_path)
    with client:
        assert client.get('/api/workspaces',headers={'host':'evil.example:8765'}).status_code==403
        assert client.get('/api/workspaces',headers={'origin':'https://evil.example'}).status_code==403
        client.headers.pop('X-CSRF-Token')
        assert client.post('/api/workspaces',json={'name':'x'}).status_code==403
        client.cookies.clear()
        assert client.get('/api/workspaces').status_code==401


def test_api_never_echoes_keys_or_request_bodies(tmp_path,monkeypatch):
    monkeypatch.setenv('SELFDIFF_API_KEY','do-not-return-me')
    client,app=connected(tmp_path)
    with client:
        response=client.get('/api/settings')
        assert 'do-not-return-me' not in response.text
        assert response.json()['key_configured']
        response=client.post('/api/workspaces',json={'name':{'secret':'do-not-return-me'}})
        assert response.status_code==422
        assert 'do-not-return-me' not in response.text


def test_cli_dry_run_never_creates_data_dir(tmp_path):
    path=tmp_path/'a.json'
    path.write_bytes(sample())
    data=tmp_path/'unused'
    env=dict(os.environ,PYTHONPATH='src')
    result=subprocess.run([sys.executable,'-m','selfdiff.cli','import','--source','normalized','--path',str(path),'--data-dir',str(data),'--dry-run'],env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert not data.exists()
