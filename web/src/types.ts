export interface Workspace {id:string;name:string;demo:number;data_version:number}
export interface Conversation {id:string;title:string;source:string;message_count:number;first_at:string|null;last_at:string|null}
export interface Message {id:string;conversation_id:string;role:string;text:string;occurred_at:string|null;source:string;version:number;title:string}
export interface Preview {preview_id:string;conversation_count:number;message_count:number;known_time_range:string[]|null;warnings:string[]}
export interface Settings {base_url:string;model:string;configured:boolean;key_configured:boolean}
export interface Evidence {message_id:string;version:number;quote:string;relation:string;occurred_at:string|null;conversation_id:string;title:string;source:string}
export interface Insight {id:string;title:string;dimension:string;kind:string;observation:string;context:string;question:string;alternatives:string[];evidence:Evidence[];status:string;revision:number;independent_conversations:number;time_range:string[]|null;user_text:string;history:{version:number;verdict:string;text:string;reason:string;created_at:string}[]}
export interface Run {id:string;status:string;mode:string;total_batches:number;completed_batches:number;rejected_candidates:number;result:{summary?:string;classification?:string;demo?:boolean;note?:string;accepted?:number}|null}
export const dimensions:Record<string,string>={goals_values:'目标与价值',thinking_decisions:'思考与决策',learning_collaboration:'学习与协作',action_results:'行动与成果',interests:'兴趣主线',change:'阶段变化'};
export const sources:Record<string,string>={normalized:'标准 JSON / 文本（豆包、DeepSeek、千问办公等）',codex:'Codex','claude-code':'Claude Code',workbuddy:'WorkBuddy',chatgpt:'ChatGPT 官方导出','claude-web':'Claude 网页官方导出'};
export const verdicts:Record<string,string>={pending:'待你确认',confirmed:'符合',partial:'部分符合',rejected:'不符合',invalidated:'来源已删除',reopen:'重新审阅'};
export function date(value:string|null){return value?new Date(value).toLocaleDateString('zh-CN'):'时间未知';}
