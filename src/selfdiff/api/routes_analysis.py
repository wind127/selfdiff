import os
from urllib.parse import urlsplit
from fastapi import APIRouter, Request
from pydantic import Field
from selfdiff.models import StrictModel, Scope
from selfdiff.analysis.provider import Provider
from selfdiff.analysis.pipeline import prepare_analysis, execute_run
from selfdiff.analysis.jobs import create_run, get_run, cancel_run
from selfdiff.comparison import challenge, compare_periods
from selfdiff.errors import AppError

router = APIRouter(prefix='/api')


class SettingsBody(StrictModel):
    workspace_id: str
    base_url: str = Field(max_length=500)
    model: str = Field(max_length=200)


class AnalysisBody(StrictModel):
    scope: Scope
    claim: str = Field(default='', max_length=1500)
    theme: str = Field(default='', max_length=500)
    period_a: dict | None = None
    period_b: dict | None = None


def settings(request, wid=None):
    base_url, model = os.environ.get('SELFDIFF_BASE_URL', ''), os.environ.get('SELFDIFF_MODEL', '')
    if wid:
        request.app.state.repo.workspace(wid)
        with request.app.state.repo.db.transaction() as c:
            row = c.execute('SELECT base_url,model FROM provider_settings WHERE workspace_id=?', (wid,)).fetchone()
        if row:
            base_url, model = row['base_url'], row['model']
    try:
        parts = urlsplit(base_url)
        if parts.username or parts.password or parts.query or parts.fragment:
            base_url = ''
    except ValueError:
        base_url = ''
    return {'base_url': base_url, 'model': model, 'configured': bool(base_url and model), 'key_configured': bool(os.environ.get('SELFDIFF_API_KEY'))}


def provider_for(request, wid):
    config = settings(request, wid)
    if request.app.state.provider_factory:
        return request.app.state.provider_factory()
    if not config['configured']:
        raise AppError('not_configured', '请先在设置中配置模型地址和名称；密钥通过启动进程环境提供。', 409)
    return Provider(config['base_url'], config['model'])


@router.get('/settings')
def get_settings(request: Request, workspace_id: str | None = None):
    return settings(request, workspace_id)


@router.put('/settings')
def put_settings(request: Request, body: SettingsBody):
    request.app.state.repo.workspace(body.workspace_id)
    Provider(body.base_url, body.model)
    with request.app.state.repo.db.transaction() as c:
        c.execute('INSERT INTO provider_settings(workspace_id,base_url,model) VALUES(?,?,?) ON CONFLICT(workspace_id) DO UPDATE SET base_url=excluded.base_url,model=excluded.model', (body.workspace_id, body.base_url, body.model))
    return settings(request, body.workspace_id)


@router.post('/provider/test')
def test_provider(request: Request, body: Scope):
    return provider_for(request, body.workspace_id).test_connection()


@router.post('/analysis/preview')
def preview(request: Request, body: Scope):
    return prepare_analysis(request.app.state.repo, body.model_dump(exclude_none=True))


def start(request, body, mode):
    repo, scope = request.app.state.repo, body.scope.model_dump(exclude_none=True)
    if repo.workspace(scope['workspace_id'])['demo']:
        from selfdiff.demo import demo_run
        return {'id': demo_run(repo, dict(scope, claim=body.claim, theme=body.theme, period_a=body.period_a, period_b=body.period_b), mode)}
    provider = provider_for(request, scope['workspace_id'])
    if mode == 'challenge':
        rid = challenge(repo, scope, body.claim)
    elif mode == 'comparison':
        rid = compare_periods(repo, scope, body.period_a or {}, body.period_b or {}, body.theme)
    else:
        rid = create_run(repo, scope)
    request.app.state.worker.submit(execute_run, repo, rid, provider)
    return {'id': rid}


@router.post('/runs')
def analyze(request: Request, body: AnalysisBody):
    return start(request, body, 'profile')


@router.post('/challenges')
def new_challenge(request: Request, body: AnalysisBody):
    return start(request, body, 'challenge')


@router.post('/comparisons')
def new_comparison(request: Request, body: AnalysisBody):
    return start(request, body, 'comparison')


@router.get('/runs/{rid}')
def read_run(request: Request, rid: str, workspace_id: str):
    return get_run(request.app.state.repo, rid, workspace_id)


@router.post('/runs/{rid}/cancel')
def cancel(request: Request, rid: str, body: Scope):
    get_run(request.app.state.repo, rid, body.workspace_id)
    cancel_run(request.app.state.repo, rid)
    return {'cancelled': True}
