from typing import Literal
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SourceKind = Literal['normalized', 'codex', 'claude-code', 'workbuddy', 'chatgpt', 'claude-web']
Dimension = Literal['goals_values', 'thinking_decisions', 'learning_collaboration', 'action_results', 'interests', 'change']


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class MessageInput(StrictModel):
    external_id: str
    role: Literal['user', 'assistant', 'system', 'tool', 'unknown']
    text: str
    occurred_at: str | None = None
    content_kind: str = 'uncertain'
    parent_id: str | None = None


class ConversationInput(StrictModel):
    external_id: str
    title: str
    source: SourceKind
    messages: list[MessageInput]
    branch_id: str | None = None


class ParseResult(StrictModel):
    conversations: list[ConversationInput] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    unsupported_count: int = 0


class EvidenceRef(StrictModel):
    message_id: str
    version: int = Field(ge=1)
    quote: str = Field(min_length=1, max_length=4000)
    relation: Literal['support', 'counter', 'context'] = 'support'


class InsightDraft(StrictModel):
    pattern_key: str = Field(min_length=1, max_length=120)
    dimension: Dimension
    kind: Literal['recurring_blocker', 'success_condition', 'self_judgment', 'period_change', 'background']
    title: str = Field(min_length=1, max_length=160)
    observation: str = Field(min_length=1, max_length=3000)
    context: str = Field(max_length=2000)
    alternatives: list[str] = Field(default_factory=list, max_length=8)
    question: str = Field(max_length=1000)
    evidence: list[EvidenceRef] = Field(min_length=1, max_length=30)


class Scope(StrictModel):
    workspace_id: str
    source_ids: list[SourceKind] | None = None
    start: str | None = None
    end: str | None = None

    @field_validator('start', 'end')
    @classmethod
    def valid_time(cls, value):
        if value is None:
            return value
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            raise ValueError('A timezone is required')
        return parsed.astimezone(timezone.utc).isoformat()

    @model_validator(mode='after')
    def ordered(self):
        if self.start and self.end and self.start >= self.end:
            raise ValueError('Start must precede end')
        return self
