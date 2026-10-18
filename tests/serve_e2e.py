"""Test-only entry point: synthetic data and a repeatable bootstrap value."""
from pathlib import Path
import sys
import tempfile
import os
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import uvicorn
from fake_provider import start
from selfdiff.api.app import create_app

os.environ['SELFDIFF_API_KEY']='_e2e_not_a_real_key_'
fake=start()
with tempfile.TemporaryDirectory() as folder:
    app=create_app(Path(folder),8770)
    @app.middleware('http')
    async def repeat_test_bootstrap(request,call_next):
        if request.url.path=='/api/session/bootstrap':
            app.state.bootstrap='e2e-only-token'
        return await call_next(request)
    try:
        uvicorn.run(app,host='127.0.0.1',port=8770,access_log=False)
    finally:
        fake.shutdown()
        fake.server_close()
