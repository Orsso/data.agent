import type { PlotlyFigure, Question, TodoItem } from './api-types'

export interface ToolStep {
  tool_name: string
  success: boolean
  summary: string
  duration_ms: number
}

/** A single entry in the chain-of-thought timeline (thinking or tool). */
export type CotEntry =
  | { type: 'thinking'; content: string }
  | { type: 'tool'; step: ToolStep }

export interface Message {
  id: string
  backend_msg_id?: string
  role: 'user' | 'assistant'
  content: string
  cot_entries: CotEntry[]
  thinking_duration_s?: number
  asked_questions?: Question[]
  todos?: TodoItem[]
  has_figures: boolean
  figure_count: number
  is_error?: boolean
}

// streaming state (transient, not persisted)
export interface StreamingMessage {
  started_at: number
  cot_entries: CotEntry[]
  active_tool?: { name: string; args: string }
  todos?: TodoItem[]
  content: string
}

// dashboard
export interface DashboardCard {
  id: string
  type: 'chart' | 'metric'
  title: string
  code?: string
  value?: string
  fig?: PlotlyFigure | null
  position: number
}
