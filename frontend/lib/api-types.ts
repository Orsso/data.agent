// Backend-facing DTOs and event payloads.
// Field names intentionally mirror the FastAPI API/SSE payloads (snake_case).

export type JsonPrimitive = string | number | boolean | null

export interface JsonObject {
  [key: string]: JsonValue
}

export interface JsonArray extends Array<JsonValue> {}

export type JsonValue = JsonPrimitive | JsonObject | JsonArray

export interface PlotlyFigure {
  data: JsonObject[]
  layout: JsonObject
}

// sse events

export type SSEEvent =
  | ThinkingEvent
  | ToolCallEvent
  | ToolResultEvent
  | TextChunkEvent
  | AskQuestionEvent
  | ChatRenamedEvent
  | TodoUpdateEvent
  | CardProposalsEvent
  | DoneEvent

export interface ThinkingEvent {
  type: 'thinking'
  content: string
}

export interface ToolCallEvent {
  type: 'tool_call'
  tool_name: string
  args: string
}

export interface ToolResultEvent {
  type: 'tool_result'
  tool_name: string
  success: boolean
  summary: string
  duration_ms: number
}

export interface TextChunkEvent {
  type: 'text_chunk'
  chunk: string
}

export interface AskQuestionEvent {
  type: 'ask_question'
  questions: Question[]
}

export interface ChatRenamedEvent {
  type: 'chat_renamed'
  chat_id: string
  title: string
}

export interface TodoUpdateEvent {
  type: 'todo_update'
  todos: TodoItem[]
}

export interface TodoItem {
  id: string
  content: string
  status: 'pending' | 'in_progress' | 'completed'
}

export interface DoneEvent {
  type: 'done'
  pending: boolean
  content: string
  has_figures: boolean
  figure_count: number
  msg_id: string
  code?: string
  error?: string
}

// questions

export interface Choice {
  label: string
  description: string
}

export interface Question {
  question: string
  header: string
  options: Choice[]
  multi_select: boolean
  selected_answer?: string | null
}

export interface CardProposal {
  proposal_id: string
  card_id: string
  card_title: string
  current_fig: Record<string, unknown> | null
  current_code: string | null
  current_value: string | null
  proposed_fig: Record<string, unknown> | null
  proposed_code: string | null
  proposed_value: string | null
  status: 'pending' | 'accepted' | 'rejected'
}

export interface CardProposalsEvent {
  type: 'card_proposals'
  proposals: CardProposal[]
}

export interface ProjectSource {
  id: string
  name: string
  origin: string
  row_count: number
  columns: string[]
  created_at: string
}

export interface ProjectSummary {
  id: string
  name: string
  description: string | null
  status: string
  source_count: number
  source_names: string[]
  chat_count: number
  created_at: string
  updated_at: string
}

export interface ProjectInfo {
  id: string
  name: string
  description: string | null
  status: string
  model: string
  suggested_questions: string[]
  sources: ProjectSource[]
  chat_count: number
  created_at: string
  updated_at: string
}

export interface ChatSummary {
  id: string
  project_id: string
  title: string | null
  pending_questions?: Question[] | null
  created_at: string
  updated_at: string
}

export interface ProjectDashboardCard {
  id: string
  type: string
  title: string
  code: string | null
  value: string | null
  fig: Record<string, unknown> | null
  content: unknown[] | null
  layout: { x: number; y: number; w: number; h: number } | null
  position: number
}
