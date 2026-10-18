import argparse
import json
import sys
from pathlib import Path
from selfdiff.errors import AppError


def main(argv=None):
    parser = argparse.ArgumentParser(prog='selfdiff', description='SelfDiff · 见己 — local personal insights')
    commands = parser.add_subparsers(dest='command', required=True)
    serve = commands.add_parser('serve')
    serve.add_argument('--port', type=int, default=8765)
    serve.add_argument('--data-dir', type=Path, default=Path.home()/'.selfdiff')
    serve.add_argument('--no-open', action='store_true')
    imp = commands.add_parser('import')
    imp.add_argument('--source', required=True)
    imp.add_argument('--path', type=Path, required=True)
    imp.add_argument('--data-dir', type=Path, default=Path.home()/'.selfdiff')
    imp.add_argument('--dry-run', action='store_true')
    imp.add_argument('--workspace-id')
    args = parser.parse_args(argv)
    try:
        if args.command == 'serve':
            import uvicorn
            import webbrowser
            from selfdiff.api.app import create_app
            if not 1024 <= args.port <= 65535:
                raise AppError('port', '端口需在 1024–65535 之间。')
            app = create_app(args.data_dir, args.port)
            url = f'http://127.0.0.1:{args.port}/#token={app.state.bootstrap}'
            print('SelfDiff · only on this device\n'+url, flush=True)
            if not args.no_open:
                webbrowser.open(url)
            uvicorn.run(app, host='127.0.0.1', port=args.port, access_log=False)
        else:
            from selfdiff.sources.ingest import preview_path
            preview = preview_path(args.source, args.path)
            if args.dry_run:
                print(json.dumps(preview.public(), ensure_ascii=False))
                return 0
            from selfdiff.store.database import Database
            from selfdiff.store.repository import Repository
            db = Database(args.data_dir/'selfdiff.sqlite3')
            db.initialize()
            repo = Repository(db)
            available = [w for w in repo.workspaces() if not w['demo']]
            wid = args.workspace_id or (available[0]['id'] if available else repo.create_workspace('我的资料')['id'])
            print(json.dumps(repo.import_preview(wid, preview), ensure_ascii=False))
        return 0
    except AppError as exc:
        print(exc.message, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
