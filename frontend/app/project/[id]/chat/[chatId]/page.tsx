'use client'

import { useCallback, useEffect, useRef } from 'react'
import { useParams } from 'next/navigation'
import Image from 'next/image'
import { AlertCircle } from 'lucide-react'
import { motion, AnimatePresence, type Variants } from 'motion/react'

import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from '@/components/ai-elements/conversation'
import {
  Message,
  MessageContent,
  MessageResponse,
} from '@/components/ai-elements/message'
import {
  PromptInput,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputSubmit,
} from '@/components/ai-elements/prompt-input'
import { ThinkingBlock } from '@/components/chat/thinking-block'
import { TodoBlock } from '@/components/chat/todo-block'
import { MessageFigures } from '@/components/chat/message-figures'
import { QuestionInput } from '@/components/chat/question-input'
import { PulsingDots } from '@/components/ui/pulsing-dots'

import { useProjectStore } from '@/lib/stores/project-store'
import { useChatsStore } from '@/lib/stores/chats-store'
import { useChatStore } from '@/lib/stores/chat-store'
import { useProjectChat } from '@/lib/hooks/use-project-chat'
import { listMessages } from '@/lib/backend-client'
import { NEW_CHAT_ID } from '@/lib/constants'

const messageVariants: Variants = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' } },
}

export default function ProjectChatPage() {
  const params = useParams()
  const projectId = params.id as string
  const chatId = params.chatId as string

  const sources = useProjectStore((s) => s.sources)
  const suggestedQuestions = useProjectStore((s) => s.suggestedQuestions)
  const isAnalyzing = useProjectStore((s) => s.isAnalyzing)

  const setActiveChatId = useChatsStore((s) => s.setActiveChatId)

  const messages = useChatStore((s) => s.messages)
  const isLoading = useChatStore((s) => s.isLoading)
  const isStreaming = useChatStore((s) => s.isStreaming)
  const streamingMessage = useChatStore((s) => s.streamingMessage)
  const pendingQuestions = useChatStore((s) => s.pendingQuestions)
  const answerQuestions = useChatStore((s) => s.answerQuestions)

  const { sendMessage, resumeChat, resolvedChatId } = useProjectChat(projectId, chatId)

  useEffect(() => {
    setActiveChatId(chatId)

    if (useChatStore.getState()._skipReset) {
      useChatStore.setState({ _skipReset: false })
      return
    }

    useChatStore.getState().reset()

    if (chatId === NEW_CHAT_ID) return

    // Real chat — fetch message history
    useChatStore.setState({ isLoading: true })
    listMessages(projectId, chatId)
      .then((items) => {
        if (items.length > 0) {
          useChatStore.getState().loadMessages(items)
        } else {
          useChatStore.setState({ isLoading: false })
        }
      })
      .catch((err) => {
        console.error(err)
        useChatStore.setState({ isLoading: false })
      })
  }, [projectId, chatId, setActiveChatId])

  const handleSubmit = useCallback(
    async ({ text }: { text: string }) => {
      if (!text.trim()) return
      await sendMessage(text.trim())
    },
    [sendMessage]
  )

  const handleSuggestionClick = useCallback(
    (suggestion: string) => {
      sendMessage(suggestion)
    },
    [sendMessage]
  )

  const handleQuestionSubmit = useCallback(
    (answers: Record<string, string>) => {
      const answerText = Object.values(answers).join(', ')
      answerQuestions(answerText)
      resumeChat(answers)
    },
    [answerQuestions, resumeChat]
  )

  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (!isStreaming && !pendingQuestions) {
      textareaRef.current?.focus()
    }
  }, [isStreaming, pendingQuestions])

  const hasSources = sources.length > 0
  const showAnalyzing = isAnalyzing && messages.length === 0 && !isLoading
  const showSuggestions = hasSources && messages.length === 0 && !isAnalyzing && !isLoading && suggestedQuestions.length > 0
  const showWelcome = !hasSources && messages.length === 0 && !isAnalyzing && !isStreaming && !isLoading
  const showWaitingIndicator = isStreaming && streamingMessage
    && (streamingMessage.cot_entries ?? []).length === 0 && !streamingMessage.content
    && !streamingMessage.active_tool

  const placeholderText = hasSources
    ? 'Ask a question about your data...'
    : 'Ask me anything, or upload data to analyze...'

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <Conversation className="flex-1">
        <ConversationContent className="mx-auto max-w-3xl py-6">
          {isLoading && (
            <div className="flex items-center justify-center py-16">
              <PulsingDots />
            </div>
          )}

          {showAnalyzing && (
            <div className="flex items-center justify-center py-16">
              <Image
                src="/icons/data-loading.svg"
                alt=""
                width={96}
                height={96}
                className="h-24 w-auto"
              />
            </div>
          )}

          {showWelcome && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <h2 className="text-xl font-semibold text-primary mb-2 font-everett">
                Welcome!
              </h2>
              <p className="text-muted-foreground max-w-md">
                Upload data to analyze, or just ask me anything about data analysis, statistics, or visualization.
              </p>
            </div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                variants={messageVariants}
                initial="hidden"
                animate="visible"
                layout
              >
                <Message from={msg.role}>
                  {msg.role === 'assistant' && (
                    <ThinkingBlock
                      cotEntries={msg.cot_entries}
                      thinkingDurationS={msg.thinking_duration_s}
                    />
                  )}
                  {msg.role === 'assistant' && msg.todos && msg.todos.length > 0 && (
                    <TodoBlock todos={msg.todos} />
                  )}
                  {msg.content && msg.is_error ? (
                    <div className="flex items-start gap-2 rounded-2xl border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
                      <AlertCircle className="mt-0.5 size-4 shrink-0" />
                      <span>{msg.content}</span>
                    </div>
                  ) : msg.content ? (
                    <MessageContent>
                      <MessageResponse>{msg.content}</MessageResponse>
                      {msg.has_figures && msg.figure_count > 0 && (
                        <MessageFigures
                          projectId={projectId}
                          chatId={resolvedChatId}
                          messageId={msg.backend_msg_id || msg.id}
                          figureCount={msg.figure_count}
                        />
                      )}
                    </MessageContent>
                  ) : null}
                  {msg.asked_questions && msg.asked_questions.length > 0 && (
                    <div className="space-y-3 py-1">
                      {msg.asked_questions.map((q, qi) => (
                        <div key={qi} className="space-y-2">
                          <p className="text-sm font-medium">{q.question}</p>
                          <div className="flex flex-wrap gap-1.5">
                            {q.options.map((opt, oi) => (
                              <span
                                key={oi}
                                className="inline-flex rounded-md border border-border/50 px-2 py-1 text-xs text-muted-foreground"
                              >
                                {opt.label}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </Message>
              </motion.div>
            ))}
          </AnimatePresence>

          {showWaitingIndicator && (
            <Message from="assistant">
              <PulsingDots />
            </Message>
          )}

          {isStreaming && streamingMessage && !showWaitingIndicator && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Message from="assistant">
                <ThinkingBlock
                  cotEntries={streamingMessage.cot_entries}
                  activeTool={streamingMessage.active_tool}
                  isStreaming
                />
                {streamingMessage.todos && streamingMessage.todos.length > 0 && (
                  <TodoBlock todos={streamingMessage.todos} isStreaming />
                )}
                {streamingMessage.content && (
                  <MessageContent>
                    <MessageResponse>
                      {streamingMessage.content}
                    </MessageResponse>
                    <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-primary" />
                  </MessageContent>
                )}
              </Message>
            </motion.div>
          )}

          {pendingQuestions && (
            <Message from="assistant">
              <QuestionInput
                questions={pendingQuestions}
                onSubmit={handleQuestionSubmit}
              />
            </Message>
          )}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      <div className="bg-gradient-to-t from-background via-background to-transparent px-4 pb-4 pt-2">
        <div className="mx-auto max-w-3xl">
          {showSuggestions && (
            <div className="grid grid-cols-2 gap-2 pb-3">
              {suggestedQuestions.map((q, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleSuggestionClick(q)}
                  className="rounded-lg border border-border/60 bg-card px-3 py-2 text-left text-sm text-foreground shadow-sm transition-all hover:border-primary/30 hover:shadow-md"
                >
                  {q}
                </button>
              ))}
            </div>
          )}
          <div className="rounded-xl border border-border/40 bg-card shadow-lg">
            <PromptInput onSubmit={handleSubmit}>
              <PromptInputTextarea
                ref={textareaRef}
                placeholder={placeholderText}
                disabled={isStreaming || !!pendingQuestions}
                className="border-0 bg-transparent focus-visible:ring-0"
              />
              <PromptInputFooter>
                <div />
                <PromptInputSubmit
                  disabled={isStreaming || !!pendingQuestions}
                  className="bg-primary hover:bg-primary/90"
                />
              </PromptInputFooter>
            </PromptInput>
          </div>
        </div>
      </div>
    </div>
  )
}
