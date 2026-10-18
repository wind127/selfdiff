import asyncio
from pathlib import Path
from fastapi import APIRouter, Request
from pydantic import Field
from selfdiff.models import StrictModel
from selfdiff.errors import AppError
from selfdiff.sources.ingest import preview_upload, preview_path, MAX_FILE

router = APIRouter(prefix='/api')


class WorkspaceBody(StrictModel):
    name: str = Field(min_length=1, max_length=120)


class WorkspaceRef(StrictModel):
    workspace_id: str


class PathBody(WorkspaceRef):
    source: str
    path: str = Field(max_length=4096)


@router.get('/workspaces')
def workspaces(request: Request):
    return request.app.state.repo.workspaces()


@router.post('/workspaces')
def new_workspace(request: Request, body: WorkspaceBody):
    return request.app.state.repo.create_workspace(body.name)


@router.post('/demo')
def new_demo(request: Request):
    from selfdiff.demo import create_demo_workspace
    return {'id': create_demo_workspace(request.app.state.repo)}


def remember(request, wid, preview):
    request.app.state.repo.workspace(wid)
    previews = request.app.state.previews
    if len(previews) >= 3:
        del previews[next(iter(previews))]
    previews[preview.preview_id] = (wid, preview)
    return preview.public()


@router.post('/imports/preview')
async def upload(request: Request, workspace_id: str, source: str, filename: str):
    request.app.state.repo.workspace(workspace_id)
    data = bytearray()
    async for part in request.stream():
        data.extend(part)
        if len(data) > MAX_FILE:
            raise AppError('limit', '单文件超过 50 MiB。', 413)
    preview = await asyncio.to_thread(preview_upload, source, Path(filename).name, bytes(data))
    return remember(request, workspace_id, preview)


@router.post('/imports/path-preview')
def path_import(request: Request, body: PathBody):
    request.app.state.repo.workspace(body.workspace_id)
    return remember(request, body.workspace_id, preview_path(body.source, Path(body.path)))


@router.post('/imports/{preview_id}/confirm')
def confirm(request: Request, preview_id: str, body: WorkspaceRef):
    item = request.app.state.previews.get(preview_id)
    if not item or item[0] != body.workspace_id:
        raise AppError('preview', '导入预览已过期或不属于当前资料空间。', 404)
    result = request.app.state.repo.import_preview(body.workspace_id, item[1])
    del request.app.state.previews[preview_id]
    return result


@router.get('/conversations')
def conversations(request: Request, workspace_id: str):
    return request.app.state.repo.conversations(workspace_id)


@router.get('/messages')
def messages(request: Request, workspace_id: str, query: str = '', conversation_id: str | None = None, cursor: int = 0, limit: int = 100):
    return request.app.state.repo.messages(workspace_id, query[:1000], cursor, min(limit, 500), conversation_id)


@router.delete('/conversations/{cid}')
def delete(request: Request, cid: str, workspace_id: str):
    # Clear unconfirmed previews as they could otherwise reintroduce deleted text.
    request.app.state.previews.clear()
    return request.app.state.repo.delete_conversation(workspace_id, cid)
