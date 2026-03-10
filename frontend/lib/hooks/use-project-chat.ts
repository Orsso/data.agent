import { useCallback, useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'

import { streamProjectChat, streamProjectResume } from '../backend-client'
import { useChatStore } from '../stores/chat-store'
import { useChatsStore } from '../stores/chats-store'
import type { SSEEvent } from '../api-types'
import type { ToolStep } from '../domain-types'
import { NEW_CHAT_ID } from '../constants'

export function useProjectChat(projectId: string, chatId: string) {
  const router = useRouter()
  const resolvedChatIdRef = useRef(chatId)
  const [resolvedChatId, setResolvedChatId] = useState(chatId)

  useEffect(() => {
    resolvedChatIdRef.current = chatId
    setResolvedChatId(chatId)
  }, [chatId])

  const processEvents = useCallback(
    async (eventStream: AsyncGenerator<SSEEvent>) => {
      const store = useChatStore.getState()
      store.startStreaming()

      try {
        for await (const event of eventStream) {
          const s = useChatStore.getState()
          switch (event.type) {
            case 'thinking':
              s.appendThinking(event.content)
              break
            case 'tool_call':
              s.setActiveTool(event.tool_name, event.args)
              break
            case 'tool_result': {
              const step: ToolStep = {
                tool_name: event.tool_name,
                success: event.success,
                summary: event.summary,
                duration_ms: event.duration_ms,
              }
              s.addToolResult(step)
              break
            }
            case 'text_chunk':
              s.appendContent(event.chunk)
              break
            case 'ask_question':
              s.setPendingQuestions(event.questions)
              break
            case 'todo_update':
              s.setTodos(event.todos)
              break
            case 'card_proposals':
              s.setProposals(event.proposals)
              break
            case 'chat_renamed':
              useChatsStore.getState().renameChat(event.chat_id, event.title)
              break
            case 'done':
              s.finishStreaming(event.content, event.has_figures, event.figure_count, event.msg_id, event.code, event.error)
              break
          }
        }
      } catch (err) {
        const detail = err instanceof Error ? err.message : 'Connection lost'
        useChatStore.getState().finishStreaming(
          `Something went wrong: ${detail}`,
          false,
          0,
          undefined,
          detail,
        )
      }
    },
    []
  )

  const sendMessage = useCallback(
    async (content: string, selectedCardIds?: string[]) => {
      let actualChatId = resolvedChatIdRef.current

      // Virtual "new" chat — create the real chat first
      if (actualChatId === NEW_CHAT_ID) {
        const chat = await useChatsStore.getState().createChat(projectId)
        actualChatId = chat.id
        resolvedChatIdRef.current = chat.id
        setResolvedChatId(chat.id)
        useChatStore.setState({ _skipReset: true })
        router.replace(`/project/${projectId}/chat/${chat.id}`)
      }

      useChatStore.getState().addUserMessage(content)
      const events = streamProjectChat(projectId, actualChatId, content, selectedCardIds)
      await processEvents(events)
    },
    [projectId, router, processEvents]
  )

  const resumeChat = useCallback(
    async (answers: Record<string, string>) => {
      useChatStore.getState().setPendingQuestions(null)
      const events = streamProjectResume(projectId, resolvedChatIdRef.current, answers)
      await processEvents(events)
    },
    [projectId, processEvents]
  )

  return { sendMessage, resumeChat, resolvedChatId }
}
