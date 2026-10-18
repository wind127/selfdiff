import pytest
from pydantic import ValidationError
from selfdiff.store.repository import Repository
from selfdiff.sources.ingest import preview_upload
from selfdiff.models import Scope
from selfdiff.evidence import validate_evidence
from selfdiff.analysis.jobs import create_run, get_run
from selfdiff.analysis.pipeline import execute_run
from test_repository import sample
from test_insights import prepared
from test_analysis import FixedProvider


def test_old_message_version_preserves_its_speaker(db):
    repo=Repository(db)
    w=repo.create_workspace('w')['id']
    repo.import_preview(w,preview_upload('normalized','x.json',sample(role='assistant')))
    mid=repo.messages(w)[0]['id']
    repo.import_preview(w,preview_upload('normalized','x.json',sample('我现在在说另一件事。')))
    assert repo.message(w,mid,1)['role']=='assistant'
    assert not validate_evidence(repo,w,[{'message_id':mid,'version':1,'quote':'我喜欢先做小版本。','relation':'support'}])['valid']


def test_invalid_and_reversed_scope_dates_are_rejected():
    for values in [{'start':'tomorrow'},{'start':'2026-02-01T00:00:00Z','end':'2026-01-01T00:00:00Z'}]:
        with pytest.raises(ValidationError):
            Scope(workspace_id='w',**values)


def test_source_update_interrupts_running_analysis(db):
    repo,w,draft=prepared(db)
    rid=create_run(repo,{'workspace_id':w})
    action=lambda: repo.import_preview(w,preview_upload('normalized','extra.json',sample(cid='extra')))
    execute_run(repo,rid,FixedProvider(draft,action))
    assert get_run(repo,rid)['status']=='interrupted'


def test_environment_provider_url_never_echoes_credentials(tmp_path,monkeypatch):
    from test_api import connected
    monkeypatch.setenv('SELFDIFF_BASE_URL','https://user:private-pass@example.com/v1?api_key=private-token')
    client,app=connected(tmp_path)
    with client:
        result=client.get('/api/settings')
        assert 'private-pass' not in result.text and 'private-token' not in result.text
