import { create } from 'zustand'

import type {
  CotEntry,
  Message,
  StreamingMessage,
  ToolStep,
} from '../domain-types'
import type { CardProposal, Question, TodoItem } from '../api-types'
import type { MessageHistoryItem } from '../backend-client'

interface ChatState {
  messages: Message[]
  isLoading: boolean
  isStreaming: boolean
  streamingMessage: StreamingMessage | null
  pendingQuestions: Question[] | null
  _skipReset: boolean

  // streaming
  startStreaming: () => void
  appendThinking: (content: string) => void
  setActiveTool: (name: string, args: string) => void
  addToolResult: (step: ToolStep) => void
  setTodos: (todos: TodoItem[]) => void
  setProposals: (proposals: CardProposal[]) => void
  appendContent: (chunk: string) => void
  finishStreaming: (content: string, hasFigures: boolean, figureCount: number, msgId?: string, code?: string, error?: string) => void
  setPendingQuestions: (questions: Question[] | null) => void

  // messages
  addUserMessage: (content: string) => void
  answerQuestions: (answers: Record<string, string>) => void
  loadMessages: (items: MessageHistoryItem[]) => void
  updateProposalStatus: (msgId: string, proposalId: string, status: 'accepted' | 'rejected') => void

  // reset
  reset: () => void
}

const initialState = {
  messages: [] as Message[],
  isLoading: false,
  isStreaming: false,
  streamingMessage: null as StreamingMessage | null,
  pendingQuestions: null as Question[] | null,
  _skipReset: false,
}

export const useChatStore = create<ChatState>()((set, get) => ({
  ...initialState,

  startStreaming: () => set({
    isStreaming: true,
    streamingMessage: { started_at: Date.now(), cot_entries: [], content: '' },
  }),

  appendThinking: (content) => set((state) => {
    if (!state.streamingMessage) return {}
    const entries: CotEntry[] = [...state.streamingMessage.cot_entries]
    const last = entries[entries.length - 1]
    if (last && last.type === 'thinking') {
      entries[entries.length - 1] = { type: 'thinking', content: last.content + content }
    } else {
      entries.push({ type: 'thinking', content })
    }
    return { streamingMessage: { ...state.streamingMessage, cot_entries: entries } }
  }),

  setActiveTool: (name, args) => set((state) => ({
    streamingMessage: state.streamingMessage
      ? { ...state.streamingMessage, active_tool: { name, args } }
      : null,
  })),

  addToolResult: (step) => set((state) => ({
    streamingMessage: state.streamingMessage
      ? {
        ...state.streamingMessage,
        cot_entries: [...state.streamingMessage.cot_entries, { type: 'tool', step }],
        active_tool: undefined,
      }
      : null,
  })),

  setTodos: (todos) => set((state) => ({
    streamingMessage: state.streamingMessage
      ? { ...state.streamingMessage, todos }
      : null,
  })),

  setProposals: (proposals) => set((state) => ({
    streamingMessage: state.streamingMessage
      ? { ...state.streamingMessage, proposals }
      : null,
  })),

  appendContent: (chunk) => set((state) => ({
    streamingMessage: state.streamingMessage
      ? { ...state.streamingMessage, content: state.streamingMessage.content + chunk }
      : null,
  })),

  finishStreaming: (content, hasFigures, figureCount, msgId, code, error) => {
    const state = get()
    const streaming = state.streamingMessage
    if (!streaming) return

    const entries = streaming.cot_entries
    const hadThinkingOrTools = entries.length > 0
    const thinkingDurationS = hadThinkingOrTools
      ? (Date.now() - streaming.started_at) / 1000
      : undefined

    const newMessage: Message = {
      id: crypto.randomUUID(),
      backend_msg_id: msgId,
      role: 'assistant',
      content,
      code: code ?? undefined,
      cot_entries: entries,
      thinking_duration_s: thinkingDurationS,
      todos: streaming.todos,
      has_figures: hasFigures,
      figure_count: figureCount,
      proposals: streaming.proposals,
      asked_questions: state.pendingQuestions ?? undefined,
      is_error: !!error,
    }

    set({
      messages: [...state.messages, newMessage],
      isStreaming: false,
      streamingMessage: null,
    })
  },

  setPendingQuestions: (questions) => set({ pendingQuestions: questions }),

  addUserMessage: (content) => set((state) => ({
    messages: [
      ...state.messages,
      {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        cot_entries: [],
        has_figures: false,
        figure_count: 0,
      },
    ],
  })),

  answerQuestions: (answers: Record<string, string>) => {
    const state = get()
    const messages = [...state.messages]

    // Find the last assistant message with asked_questions and set selected_answer
    for (let i = messages.length - 1; i >= 0; i--) {
      const msg = messages[i]
      if (msg.role === 'assistant' && msg.asked_questions) {
        messages[i] = {
          ...msg,
          asked_questions: msg.asked_questions.map((q) =>
            answers[q.question] ? { ...q, selected_answer: answers[q.question] } : q
          ),
        }
        break
      }
    }

    set({
      messages,
      pendingQuestions: null,
    })
  },

  loadMessages: (items) => set({
    isLoading: false,
    messages: items.map((item) => {
      const entries: CotEntry[] = []
      if (item.thinking) {
        entries.push({ type: 'thinking', content: item.thinking })
      }
      if (item.tool_steps) {
        for (const s of item.tool_steps) {
          entries.push({
            type: 'tool',
            step: {
              tool_name: s.tool_name,
              summary: s.summary,
              success: s.success,
              duration_ms: s.duration_ms,
            },
          })
        }
      }
      return {
        id: item.id,
        backend_msg_id: item.id,
        role: item.role as 'user' | 'assistant',
        content: item.content,
        code: item.code ?? undefined,
        cot_entries: entries,
        thinking_duration_s: item.thinking_duration_s ?? undefined,
        todos: item.todos ?? undefined,
        has_figures: item.figure_count > 0,
        figure_count: item.figure_count,
        proposals: item.proposals ?? undefined,
        asked_questions: item.asked_questions ?? undefined,
      }
    }),
  }),

  updateProposalStatus: (msgId, proposalId, status) => set((state) => ({
    messages: state.messages.map((msg) => {
      if (msg.backend_msg_id !== msgId || !msg.proposals) return msg
      return {
        ...msg,
        proposals: msg.proposals.map((p) =>
          p.proposal_id === proposalId ? { ...p, status } : p
        ),
      }
    }),
  })),

  reset: () => set(initialState),
}))
