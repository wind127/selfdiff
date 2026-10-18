import json
import httpx
import pytest
from selfdiff.analysis.provider import Provider
from selfdiff.analysis.pipeline import prepare_analysis, execute_run
from selfdiff.analysis.jobs import create_run, get_run, cancel_run, interrupt_runs
from selfdiff.errors import AppError
from selfdiff.insights import list_insights
from test_insights import prepared


class FixedProvider:
    def __init__(self, draft, action=None):
        self.draft, self.action = draft, action

    def complete_json(self, messages, schema):
        if self.action:
            action, self.action = self.action, None
            action()
        return {'insights': [self.draft]}


def test_pipeline_persists_valid_insights_and_coverage(db):
    repo, w, draft = prepared(db)
    scope = {'workspace_id': w}
    assert prepare_analysis(repo, scope)['message_count'] == 2
    rid = create_run(repo, scope)
    execute_run(repo, rid, FixedProvider(draft))
    run = get_run(repo, rid)
    assert run['status'] == 'succeeded'
    assert run['completed_batches'] == run['total_batches'] == 1
    assert len(list_insights(repo, w)) == 1


def test_fabricated_quotes_rejected(db):
    repo, w, draft = prepared(db)
    draft['evidence'][0]['quote'] = '伪造的话'
    rid = create_run(repo, {'workspace_id': w})
    execute_run(repo, rid, FixedProvider(draft))
    assert get_run(repo, rid)['rejected_candidates'] > 0
    assert list_insights(repo, w) == []


@pytest.mark.parametrize('delete', [False, True])
def test_cancel_and_concurrent_delete_cannot_write(db, delete):
    repo, w, draft = prepared(db)
    rid = create_run(repo, {'workspace_id': w})
    action = lambda: repo.delete_conversation(w, repo.conversations(w)[0]['id']) if delete else cancel_run(repo, rid)
    execute_run(repo, rid, FixedProvider(draft, action))
    assert get_run(repo, rid)['status'] == 'cancelled'
    assert list_insights(repo, w) == []


def test_restart_interrupts_without_provider_calls(db):
    repo, w, _ = prepared(db)
    rid = create_run(repo, {'workspace_id': w})
    interrupt_runs(repo)
    assert get_run(repo, rid)['status'] == 'interrupted'


def test_provider_bounded_schema_repair_and_no_secret_errors():
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(200, json={'choices': [{'message': {'content': 'not-json'}}]})
    provider = Provider('https://model.example/v1', 'test', 'secret', transport=httpx.MockTransport(handle))
    with pytest.raises(AppError) as exc:
        provider.complete_json([{'role': 'user', 'content': 'private'}], {'type': 'object'})
    assert len(calls) == 2
    assert 'private' not in str(exc.value) and 'secret' not in str(exc.value)


@pytest.mark.parametrize('url', ['https://user:pass@example.com/v1', 'https://example.com/v1?key=secret', 'http://external.example/v1'])
def test_provider_rejects_credential_urls(url):
    with pytest.raises(AppError):
        Provider(url, 'model', '')
