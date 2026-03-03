import type {
  ChatSummary,
  PlotlyFigure,
  ProjectDashboardCard,
  ProjectInfo,
  ProjectSource,
  ProjectSummary,
  SSEEvent,
  TodoItem,
} from './api-types'
import type { ToolStep } from './domain-types'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? ''

// SSE streams bypass the Next.js rewrite because rewrites can buffer and break streaming.
const STREAM_BASE =
  process.env.NEXT_PUBLIC_STREAM_BASE_URL ??
  process.env.NEXT_PUBLIC_API_ORIGIN ??
  'http://127.0.0.1:8000'

interface ApiErrorPayload {
  error?: string
  detail?: string
}

async function readErrorMessage(res: Response, fallback: string): Promise<string> {
  const payload = await res.json().catch(() => null) as ApiErrorPayload | null
  return payload?.error || payload?.detail || fallback
}

async function consumeResponseBody(res: Response): Promise<void> {
  const reader = res.body?.getReader()
  if (!reader) return

  while (true) {
    const { done } = await reader.read()
    if (done) break
  }
}

// --- Projects ---

export async function createProject(name: string): Promise<ProjectInfo> {
  const res = await fetch(`${API_BASE}/api/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error(await readErrorMessage(res, 'Failed to create project'))
  return res.json()
}

export async function listProjects(): Promise<ProjectSummary[]> {
  const res = await fetch(`${API_BASE}/api/projects`)
  if (!res.ok) throw new Error('Failed to list projects')
  const data = await res.json() as { projects: ProjectSummary[] }
  return data.projects
}

export async function getProject(projectId: string): Promise<ProjectInfo> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}`)
  if (!res.ok) throw new Error('Project not found')
  return res.json()
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(await readErrorMessage(res, 'Failed to delete project'))
}

// --- Project Sources ---

export async function addProjectSource(projectId: string, file: File): Promise<ProjectSource> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${STREAM_BASE}/api/projects/${projectId}/sources`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) throw new Error(await readErrorMessage(res, 'Failed to add source'))
  return res.json()
}

export async function removeProjectSource(projectId: string, name: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/sources/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error(await readErrorMessage(res, 'Failed to remove source'))
}

// --- Chats ---

export async function createChat(projectId: string, title?: string): Promise<ChatSummary> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/chats`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(title ? { title } : {}),
  })
  if (!res.ok) throw new Error(await readErrorMessage(res, 'Failed to create chat'))
  return res.json()
}

export async function listChats(projectId: string): Promise<ChatSummary[]> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/chats`)
  if (!res.ok) throw new Error('Failed to list chats')
  return res.json()
}

export async function renameChat(projectId: string, chatId: string, title: string): Promise<ChatSummary> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/chats/${chatId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  if (!res.ok) throw new Error(await readErrorMessage(res, 'Failed to rename chat'))
  return res.json()
}

export async function deleteChat(projectId: string, chatId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/chats/${chatId}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error(await readErrorMessage(res, 'Failed to delete chat'))
}

// --- Message History ---

export interface MessageHistoryItem {
  id: string
  role: 'user' | 'assistant'
  content: string
  thinking: string | null
  thinking_duration_s: number | null
  tool_steps: ToolStep[] | null
  figure_count: number
  todos: TodoItem[] | null
  created_at: string
}

export async function listMessages(
  projectId: string,
  chatId: string
): Promise<MessageHistoryItem[]> {
  const res = await fetch(
    `${API_BASE}/api/projects/${projectId}/chats/${chatId}/messages`
  )
  if (!res.ok) return []
  return res.json()
}

// --- Chat Streaming ---

export async function* streamProjectChat(
  projectId: string,
  chatId: string,
  message: string,
  selectedCardIds?: string[]
): AsyncGenerator<SSEEvent> {
  const res = await fetch(
    `${STREAM_BASE}/api/projects/${projectId}/chats/${chatId}/messages`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        selected_card_ids: selectedCardIds?.length ? selectedCardIds : null,
      }),
    }
  )
  if (!res.ok) throw new Error(await readErrorMessage(res, 'Chat failed'))
  yield* parseSSE(res)
}

export async function* streamProjectResume(
  projectId: string,
  chatId: string,
  answers: Record<string, string>
): AsyncGenerator<SSEEvent> {
  const res = await fetch(
    `${STREAM_BASE}/api/projects/${projectId}/chats/${chatId}/messages/resume`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers }),
    }
  )
  if (!res.ok) throw new Error(await readErrorMessage(res, 'Resume failed'))
  yield* parseSSE(res)
}

async function* parseSSE(res: Response): AsyncGenerator<SSEEvent> {
  const reader = res.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event = JSON.parse(line.slice(6)) as SSEEvent
          yield event
        } catch {
          // ignore malformed events
        }
      }
    }
  }

  if (buffer.startsWith('data: ')) {
    try {
      yield JSON.parse(buffer.slice(6)) as SSEEvent
    } catch {
      // ignore
    }
  }
}

export async function getProjectMessageFigures(
  projectId: string,
  chatId: string,
  messageId: string
): Promise<PlotlyFigure[]> {
  const res = await fetch(
    `${API_BASE}/api/projects/${projectId}/chats/${chatId}/messages/${messageId}/figures`
  )
  if (!res.ok) {
    console.error(`Failed to fetch figures: ${res.status} ${res.statusText}`)
    return []
  }
  return res.json()
}

// --- Project Pipelines ---

export async function runProjectInsights(projectId: string): Promise<ProjectInfo> {
  const res = await fetch(`${STREAM_BASE}/api/projects/${projectId}/pipelines/insights`, {
    method: 'POST',
  })
  if (!res.ok) throw new Error(await readErrorMessage(res, 'Insights pipeline failed'))
  await consumeResponseBody(res)
  return getProject(projectId)
}

export async function runProjectDashboard(projectId: string): Promise<ProjectDashboardCard[]> {
  const res = await fetch(`${STREAM_BASE}/api/projects/${projectId}/pipelines/dashboard`, {
    method: 'POST',
  })
  if (!res.ok) throw new Error(await readErrorMessage(res, 'Dashboard pipeline failed'))
  await consumeResponseBody(res)
  return getProjectDashboardCards(projectId)
}

export async function getProjectDashboardCards(projectId: string): Promise<ProjectDashboardCard[]> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/dashboard-cards`)
  if (!res.ok) throw new Error('Failed to fetch dashboard cards')
  return res.json()
}

export async function addDashboardCard(
  projectId: string,
  card: { type: string; title: string; code?: string | null; value?: string | null; fig?: Record<string, unknown> | null }
): Promise<ProjectDashboardCard> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/dashboard-cards`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(card),
  })
  if (!res.ok) throw new Error(await readErrorMessage(res, 'Failed to add dashboard card'))
  return res.json()
}

export async function removeDashboardCard(projectId: string, cardId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/dashboard-cards/${cardId}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error(await readErrorMessage(res, 'Failed to remove dashboard card'))
}
