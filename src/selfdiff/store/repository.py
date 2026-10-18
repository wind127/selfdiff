import json
import time
import uuid
from hashlib import sha256
from selfdiff.errors import AppError
from selfdiff.sources.ingest import preview_path


def uid():
    return uuid.uuid4().hex


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


class Repository:
    def __init__(self, database):
        self.db = database

    def create_workspace(self, name, demo=False):
        wid = uid()
        with self.db.transaction() as c:
            c.execute('INSERT INTO workspaces(id,name,demo) VALUES(?,?,?)', (wid, name[:120], demo))
        return self.workspace(wid)

    def workspaces(self):
        with self.db.transaction() as c:
            return [dict(r) for r in c.execute('SELECT * FROM workspaces ORDER BY created_at,id')]

    def workspace(self, wid):
        with self.db.transaction() as c:
            row = c.execute('SELECT * FROM workspaces WHERE id=?', (wid,)).fetchone()
            if not row:
                raise AppError('not_found', '资料空间不存在。', 404)
            return dict(row)

    def import_preview(self, wid, preview):
        self.workspace(wid)
        if time.time() - preview.created_at > 1800:
            raise AppError('expired', '预览已过期，请重新选择资料。')
        if preview.path and preview_path(preview.source, preview.path).input_hash != preview.input_hash:
            raise AppError('changed', '资料在预览后发生变化，请重新预览。', 409)
        summary = dict(added_conversations=0, added_messages=0, updated_messages=0, unchanged_messages=0, warnings=preview.warnings)
        with self.db.transaction() as c:
            for item in preview.conversations:
                row = c.execute('SELECT id FROM conversations WHERE workspace_id=? AND source=? AND external_id=?', (wid, item.source, item.external_id)).fetchone()
                cid = row['id'] if row else uid()
                if not row:
                    c.execute('INSERT INTO conversations(id,workspace_id,source,external_id,title,branch_id) VALUES(?,?,?,?,?,?)', (cid, wid, item.source, item.external_id, item.title, item.branch_id))
                    summary['added_conversations'] += 1
                for m in item.messages:
                    old = c.execute('SELECT m.id,m.active_version,v.digest FROM messages m JOIN message_versions v ON v.message_id=m.id AND v.version=m.active_version WHERE m.conversation_id=? AND m.external_id=?', (cid, m.external_id)).fetchone()
                    digest = sha256(encoded([m.text, m.role, m.content_kind, m.occurred_at]).encode()).hexdigest()
                    if old and old['digest'] == digest:
                        summary['unchanged_messages'] += 1
                        continue
                    mid, version = (old['id'], old['active_version']+1) if old else (uid(), 1)
                    if old:
                        c.execute('UPDATE messages SET active_version=?,role=?,content_kind=?,occurred_at=? WHERE id=?', (version, m.role, m.content_kind, m.occurred_at, mid))
                        summary['updated_messages'] += 1
                    else:
                        c.execute('INSERT INTO messages(id,workspace_id,conversation_id,external_id,role,content_kind,occurred_at) VALUES(?,?,?,?,?,?,?)', (mid, wid, cid, m.external_id, m.role, m.content_kind, m.occurred_at))
                        summary['added_messages'] += 1
                    c.execute('INSERT INTO message_versions(message_id,workspace_id,version,text,digest) VALUES(?,?,?,?,?)', (mid, wid, version, m.text, digest))
            if summary['added_messages'] or summary['updated_messages']:
                c.execute('UPDATE workspaces SET data_version=data_version+1 WHERE id=?', (wid,))
            c.execute('INSERT INTO import_runs(id,workspace_id,summary) VALUES(?,?,?)', (uid(), wid, encoded(summary)))
        return summary

    def conversations(self, wid):
        self.workspace(wid)
        with self.db.transaction() as c:
            return [dict(r) for r in c.execute('SELECT c.*,count(m.id) message_count,min(m.occurred_at) first_at,max(m.occurred_at) last_at FROM conversations c LEFT JOIN messages m ON m.conversation_id=c.id WHERE c.workspace_id=? GROUP BY c.id ORDER BY last_at DESC,c.id', (wid,))]

    def messages(self, wid, query='', cursor=0, limit=1000, conversation_id=None, scope=None):
        self.workspace(wid)
        sql = 'SELECT m.id,m.conversation_id,m.role,m.content_kind,m.occurred_at,m.active_version version,v.text,c.source,c.title,c.external_id conversation_external_id,c.branch_id FROM messages m JOIN message_versions v ON v.message_id=m.id AND v.version=m.active_version JOIN conversations c ON c.id=m.conversation_id WHERE m.workspace_id=?'
        args = [wid]
        if query:
            sql += ' AND instr(lower(v.text),lower(?))>0'
            args.append(query)
        if conversation_id:
            sql += ' AND m.conversation_id=?'
            args.append(conversation_id)
        if scope:
            for key, op in [('start', '>='), ('end', '<')]:
                if scope.get(key):
                    sql += f' AND m.occurred_at {op} ?'
                    args.append(scope[key])
            if scope.get('source_ids'):
                sql += ' AND c.source IN ('+','.join('?' for _ in scope['source_ids'])+')'
                args.extend(scope['source_ids'])
        sql += ' ORDER BY m.occurred_at,m.id LIMIT ? OFFSET ?'
        args.extend([min(max(int(limit), 1), 100000), max(int(cursor), 0)])
        with self.db.transaction() as c:
            return [dict(r) for r in c.execute(sql, args)]

    def message(self, wid, mid, version):
        with self.db.transaction() as c:
            row = c.execute('SELECT m.*,v.text,v.version,c.source,c.title,c.branch_id,c.external_id conversation_external_id FROM messages m JOIN message_versions v ON v.message_id=m.id JOIN conversations c ON c.id=m.conversation_id WHERE m.workspace_id=? AND m.id=? AND v.version=?', (wid, mid, version)).fetchone()
            return dict(row) if row else None

    def delete_conversation(self, wid, cid):
        with self.db.transaction() as c:
            if not c.execute('SELECT id FROM conversations WHERE workspace_id=? AND id=?', (wid, cid)).fetchone():
                raise AppError('not_found', '会话不存在。', 404)
            # Conservatively invalidate the entire workspace's derived content.
            c.execute('DELETE FROM insight_revisions WHERE insight_id IN (SELECT id FROM insights WHERE workspace_id=?)', (wid,))
            c.execute('DELETE FROM evidence WHERE workspace_id=?', (wid,))
            c.execute("UPDATE insights SET content='{}',status='invalidated',invalidated=1 WHERE workspace_id=?", (wid,))
            c.execute("UPDATE profile_snapshots SET content='{}',invalidated=1 WHERE workspace_id=?", (wid,))
            c.execute('DELETE FROM analysis_batches WHERE workspace_id=?', (wid,))
            c.execute("UPDATE analysis_runs SET result=NULL,error=NULL,status=CASE WHEN status IN ('queued','running') THEN 'cancelled' ELSE 'interrupted' END,scope='{}' WHERE workspace_id=?", (wid,))
            c.execute('DELETE FROM conversations WHERE workspace_id=? AND id=?', (wid, cid))
            c.execute('UPDATE workspaces SET data_version=data_version+1 WHERE id=?', (wid,))
        return {'deleted': True, 'derived_content_cleared': True}
