from datetime import datetime, timezone
from html import escape
import json
from selfdiff.insights import list_insights
from selfdiff.comparison import list_snapshots
from selfdiff.errors import AppError


def export_profile(repo, wid, format):
    workspace = repo.workspace(wid)
    insights = list_insights(repo, wid, include_rejected=True)
    data = {'app': 'SelfDiff', 'version': 1, 'exported_at': datetime.now(timezone.utc).isoformat(),
            'workspace': workspace, 'insights': insights, 'snapshots': list_snapshots(repo, wid),
            'conversations': repo.conversations(wid), 'messages': repo.messages(wid, limit=100000)}
    if format == 'json':
        return json.dumps(data, ensure_ascii=False, indent=2).encode()
    if format != 'markdown':
        raise AppError('format', '支持 JSON 或 Markdown 导出。')
    lines = ['# SelfDiff · 个人洞察档案', '', '合成示例' if workspace['demo'] else '本人资料 · 含私密证据，请谨慎保存与分享', '',
             '导出时间：'+data['exported_at'], '所有发现仅反映所导入资料，需本人确认。', '']
    for item in insights:
        lines += ['## '+item['title'], '', '状态：'+item['status'], item['user_text'] or item['observation'], '', '情境：'+item['context'], '', '其他解释：'+'；'.join(item['alternatives']), '', '待确认：'+item['question'], '']
        for ref in item['evidence']:
            lines += ['> '+ref['quote'].replace('\n', '\n> '), '', f"{ref['relation']} · {ref['source']} · {ref['occurred_at'] or '时间未知'}", '']
        for revision in item['history']:
            lines += [f"### 本人修订 v{revision['version']} · {revision['verdict']}", '', revision['text'], '', '理由：'+revision['reason'], '', '记录时间：'+revision['created_at'], '']
    # The complete Markdown archive preserves the same snapshot/history payload as JSON.
    for snapshot in data['snapshots']:
        lines += ['## 历史快照 · '+snapshot['created_at'], '', '    '+json.dumps(snapshot, ensure_ascii=False).replace('\n', '\n    '), '']
    return '\n'.join(lines).encode()


def export_share_card(repo, wid, insight_ids, edited_text):
    workspace = repo.workspace(wid)
    allowed = {i['id'] for i in list_insights(repo, wid)}
    if not insight_ids or any(i not in allowed for i in insight_ids) or not edited_text.strip() or len(edited_text) > 4000:
        raise AppError('share', '请明确选择洞察并确认要公开的摘要文字。')
    badge = '合成示例 · ' if workspace['demo'] else ''
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SelfDiff</title><style>body{margin:0;background:#f3f0e8;color:#233b36;font-family:system-ui,sans-serif;padding:8vw}article{max-width:720px;margin:auto;border-top:3px solid;padding-top:24px}p{white-space:pre-wrap;font-size:24px;line-height:1.8}small{color:#6c7268}</style><article><small>'+badge+'SELFDIFF / 见己</small><h1>对自己的理解，也有了新的版本。</h1><p>'+escape(edited_text)+'</p><small>本人选择的公开摘要 · 不是心理诊断</small></article></html>'
