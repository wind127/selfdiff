from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

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
    source_ids: list[str] | None = None
    start: str | None = None
    end: str | None = None
