import secrets
from fastapi import Request
from fastapi.responses import JSONResponse


def install_security(app, port):
    app.state.bootstrap = secrets.token_urlsafe(32)
    app.state.session = secrets.token_urlsafe(32)
    app.state.csrf = secrets.token_urlsafe(32)
    allowed_hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
    allowed_origins = {'http://'+host for host in allowed_hosts}

    @app.middleware('http')
    async def boundary(request: Request, call_next):
        if request.headers.get('host') not in allowed_hosts or (request.headers.get('origin') and request.headers['origin'] not in allowed_origins):
            return JSONResponse({'code': 'origin', 'message': '仅允许本机应用访问。'}, status_code=403)
        if request.url.path.startswith('/api/') and request.url.path not in ('/api/session/bootstrap', '/api/health'):
            if not secrets.compare_digest(request.cookies.get('selfdiff_session', ''), app.state.session):
                return JSONResponse({'code': 'session', 'message': '请从终端显示的启动链接打开应用。'}, status_code=401)
            if request.method not in ('GET', 'HEAD') and not secrets.compare_digest(request.headers.get('x-csrf-token', ''), app.state.csrf):
                return JSONResponse({'code': 'csrf', 'message': '操作令牌失效，请刷新应用。'}, status_code=403)
        length = request.headers.get('content-length', '0')
        if not length.isdigit() or int(length) > 50*1024*1024:
            return JSONResponse({'code': 'limit', 'message': '请求超过 50 MiB。'}, status_code=413)
        response = await call_next(request)
        response.headers.update({'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
                                 'Cache-Control': 'no-store', 'X-Frame-Options': 'DENY',
                                 'Content-Security-Policy': "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'"})
        return response
