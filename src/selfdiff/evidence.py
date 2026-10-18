from pydantic import ValidationError
from selfdiff.models import EvidenceRef


def validate_evidence(repo, workspace_id, refs):
    records, reasons = [], []
    for raw in refs:
        try:
            ref = raw if isinstance(raw, EvidenceRef) else EvidenceRef.model_validate(raw)
        except ValidationError:
            reasons.append('invalid_reference')
            continue
        row = repo.message(workspace_id, ref.message_id, ref.version)
        if not row or not ref.quote.strip() or ref.quote not in row['text']:
            reasons.append('quote_not_found')
        elif row['role'] != 'user':
            reasons.append('not_user_authored')
        elif row['content_kind'] in ('quoted', 'hypothetical', 'tool', 'assistant', 'uncertain') and ref.relation != 'context':
            reasons.append('not_personal_evidence')
        else:
            records.append(dict(ref.model_dump(), conversation_id=row['conversation_id'], source=row['source'],
                                title=row['title'], occurred_at=row['occurred_at'], text=row['text'],
                                independent_id=row['source']+':'+(row['branch_id'] or row['conversation_external_id'])))
    return {'valid': not reasons and bool(records), 'reasons': reasons, 'records': records}
