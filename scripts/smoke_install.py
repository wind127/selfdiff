"""Install a built wheel into an empty venv and verify loopback UI assets."""
from pathlib import Path
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import venv


def main():
    root=Path(__file__).resolve().parents[1]
    wheels=list((root/(sys.argv[1] if len(sys.argv)>1 else 'dist')).glob('selfdiff-*.whl'))
    assert len(wheels)==1,'Build the release wheel before running installation smoke'
    with tempfile.TemporaryDirectory(prefix='selfdiff-smoke-') as folder:
        temp=Path(folder).resolve()
        temp.relative_to(Path(tempfile.gettempdir()).resolve())
        venv.create(temp/'venv',with_pip=True)
        python=temp/'venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        install=[str(python),'-m','pip','install','--disable-pip-version-check']
        wheelhouse=root/'.local/wheelhouse'
        if wheelhouse.exists():
            install+=['--no-index','--find-links',str(wheelhouse)]
        subprocess.run(install+[str(wheels[0])],check=True,stdout=subprocess.DEVNULL)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            port=sock.getsockname()[1]
        env=dict(os.environ)
        for key in ['PYTHONPATH','SELFDIFF_API_KEY','SELFDIFF_MODEL','SELFDIFF_BASE_URL']:
            env.pop(key,None)
        with (temp/'server.log').open('w') as log:
            process=subprocess.Popen([str(python),'-m','selfdiff.cli','serve','--port',str(port),'--data-dir',str(temp/'data'),'--no-open'],cwd=temp,env=env,stdout=log,stderr=log)
            try:
                origin=f'http://127.0.0.1:{port}'
                for _ in range(100):
                    try:
                        with urllib.request.urlopen(origin+'/api/health',timeout=1) as r:
                            assert json.load(r)['app']=='selfdiff'
                        break
                    except OSError:
                        if process.poll() is not None:
                            raise RuntimeError('Installed server failed to start')
                        time.sleep(.2)
                else:
                    raise RuntimeError('Installed server startup timed out')
                with urllib.request.urlopen(origin,timeout=5) as r:
                    html=r.read().decode()
                assert 'SelfDiff' in html
                assets=re.findall(r'(?:src|href)="(/assets/[^"]+)"',html)
                assert len(assets)>=2
                for asset in assets:
                    with urllib.request.urlopen(origin+asset,timeout=5) as r:
                        assert r.status==200 and len(r.read())>100
                print('Installed wheel smoke passed: loopback health, HTML, JS, CSS; no source path or Node runtime used.')
            finally:
                process.terminate()
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__=='__main__':
    main()
