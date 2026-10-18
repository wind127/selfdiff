from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
import secrets
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from selfdiff import __version__
from selfdiff.models import StrictModel
from selfdiff.errors import AppError
from selfdiff.store.database import Database
from selfdiff.store.repository import Repository
from selfdiff.analysis.jobs import interrupt_runs
from .security import install_security
from . import routes_library, routes_analysis, routes_profile


class BootstrapBody(StrictModel):
    token: str


def create_app(data_dir: Path, port: int = 8765, provider_factory=None):
    db = Database(Path(data_dir) / 'selfdiff.sqlite3')
    db.initialize()
    repo = Repository(db)

    @asynccontextmanager
    async def lifespan(app):
        interrupt_runs(repo)
        yield
        app.state.worker.shutdown(wait=False, cancel_futures=True)
        interrupt_runs(repo)

    app = FastAPI(title='SelfDiff', lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.repo, app.state.previews = repo, {}
    app.state.provider_factory = provider_factory
    app.state.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix='selfdiff-analysis')
    install_security(app, port)

    @app.exception_handler(AppError)
    async def domain_error(request, exc):
        return JSONResponse({'code': exc.code, 'message': exc.message}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse({'code': 'input', 'message': '输入格式不正确，请检查必填字段与长度。'}, status_code=422)

    @app.get('/api/health')
    def health():
        return {'app': 'selfdiff', 'version': __version__}

    @app.post('/api/session/bootstrap')
    def bootstrap(body: BootstrapBody):
        token = app.state.bootstrap
        if not token or not secrets.compare_digest(body.token, token):
            raise AppError('bootstrap', '启动链接已使用或失效，请使用已有会话或重启服务。', 401)
        app.state.bootstrap = None
        response = JSONResponse({'csrf': app.state.csrf})
        response.set_cookie('selfdiff_session', app.state.session, httponly=True, samesite='strict', path='/')
        return response

    @app.get('/api/session')
    def session():
        return {'csrf': app.state.csrf}

    app.include_router(routes_library.router)
    app.include_router(routes_analysis.router)
    app.include_router(routes_profile.router)
    static = Path(__file__).parent.parent / 'static'
    if (static / 'assets').exists():
        app.mount('/assets', StaticFiles(directory=static / 'assets'), name='assets')

    @app.get('/{path:path}')
    def frontend(path: str):
        if path.startswith('api/'):
            return JSONResponse({'code': 'not_found', 'message': '接口不存在。'}, status_code=404)
        if (static / 'index.html').exists():
            return FileResponse(static / 'index.html')
        return Response('SelfDiff frontend is not built. Run python scripts/build_release.py first.', status_code=503)
    return app
