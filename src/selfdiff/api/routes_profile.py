from fastapi import APIRouter, Request
from fastapi.responses import Response
from pydantic import Field
from selfdiff.models import StrictModel
from selfdiff.insights import list_insights, revise_insight
from selfdiff.comparison import save_snapshot, list_snapshots
from selfdiff.exports import export_profile, export_share_card

router = APIRouter(prefix='/api')


class RevisionBody(StrictModel):
    workspace_id: str
    verdict: str
    text: str = Field(default='', max_length=4000)
    reason: str = Field(default='', max_length=2000)
    expected_revision: int


class ShareBody(StrictModel):
    workspace_id: str
    insight_ids: list[str]
    text: str = Field(max_length=4000)


class SnapshotBody(StrictModel):
    workspace_id: str
    run_id: str


@router.get('/insights')
def insights(request: Request, workspace_id: str, include_rejected: bool = False):
    return list_insights(request.app.state.repo, workspace_id, include_rejected)


@router.post('/insights/{iid}/revisions')
def revise(request: Request, iid: str, body: RevisionBody):
    return revise_insight(request.app.state.repo, body.workspace_id, iid, body.verdict, body.text, body.reason, body.expected_revision)


@router.get('/snapshots')
def snapshots(request: Request, workspace_id: str):
    request.app.state.repo.workspace(workspace_id)
    return list_snapshots(request.app.state.repo, workspace_id)


@router.post('/snapshots')
def snapshot(request: Request, body: SnapshotBody):
    return {'id': save_snapshot(request.app.state.repo, body.workspace_id, body.run_id)}


@router.get('/exports')
def export(request: Request, workspace_id: str, format: str = 'json'):
    return Response(export_profile(request.app.state.repo, workspace_id, format), media_type='application/json' if format == 'json' else 'text/markdown', headers={'Content-Disposition': f'attachment; filename="selfdiff.{"json" if format == "json" else "md"}"'})


@router.post('/exports/share')
def share(request: Request, body: ShareBody):
    return Response(export_share_card(request.app.state.repo, body.workspace_id, body.insight_ids, body.text), media_type='text/html', headers={'Content-Disposition': 'attachment; filename="selfdiff-card.html"'})
