'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'next/navigation'
import { AlertCircle, Sparkles } from 'lucide-react'
import { motion, AnimatePresence, LayoutGroup, type Variants } from 'motion/react'

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
import { CardProposals } from '@/components/chat/card-proposals'
import { CardSelectionChips } from '@/components/chat/card-selection-chips'
import { QuestionInput } from '@/components/chat/question-input'
import { PulsingDots } from '@/components/ui/pulsing-dots'
import { BrandLogo } from '@/components/shared/brand-logo'

import { useProjectStore } from '@/lib/stores/project-store'
import { useChatsStore } from '@/lib/stores/chats-store'
import { useChatStore } from '@/lib/stores/chat-store'
import { useDashboardStore } from '@/lib/stores/dashboard-store'
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

  const { sendMessage, resumeChat, resolvedChatId } = useProjectChat(projectId, chatId)
  const clearSelection = useDashboardStore((s) => s.clearSelection)

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
      const { selectedCardIds: cardIds } = useDashboardStore.getState()
      const ids = cardIds.length > 0 ? [...cardIds] : undefined
      clearSelection()
      await sendMessage(text.trim(), ids)
    },
    [sendMessage, clearSelection]
  )

  const handleSuggestionClick = useCallback(
    (suggestion: string) => {
      sendMessage(suggestion)
    },
    [sendMessage]
  )

  const handleQuestionSubmit = useCallback(
    (answers: Record<string, string>) => {
      useChatStore.getState().answerQuestions(answers)
      resumeChat(answers)
    },
    [resumeChat]
  )

  // Detect if the last message has unanswered questions
  const lastMsg = messages[messages.length - 1]
  const hasPendingQuestions = !!(
    lastMsg?.role === 'assistant' &&
    lastMsg.asked_questions?.length &&
    lastMsg.asked_questions.some((q) => !q.selected_answer)
  )

  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (!isStreaming && !hasPendingQuestions) {
      textareaRef.current?.focus()
    }
  }, [isStreaming, hasPendingQuestions])

  // Track whether we went through the analyzing phase, so we only
  // animate suggestion chips when they replace skeletons (not on reload).
  // Uses the "set state during render" pattern (React 19 compliant).
  const [wasAnalyzing, setWasAnalyzing] = useState(false)

  const hasSources = sources.length > 0
  const isEmpty = messages.length === 0 && !isStreaming && !isLoading
  const showAnalyzing = isAnalyzing && isEmpty
  if (showAnalyzing && !wasAnalyzing) setWasAnalyzing(true)
  const showSuggestions = hasSources && isEmpty && !isAnalyzing && suggestedQuestions.length > 0
  const showWelcome = !hasSources && isEmpty && !isAnalyzing
  const showWaitingIndicator = isStreaming && streamingMessage
    && (streamingMessage.cot_entries ?? []).length === 0 && !streamingMessage.content
    && !streamingMessage.active_tool

  const placeholderText = hasSources
    ? 'Ask a question about your data...'
    : 'Ask me anything, or upload data to analyze...'

  // ── Prompt bar (shared via layoutId for smooth position animation) ──
  const promptBar = (
    <motion.div
      layoutId="prompt-bar"
      layout="position"
      transition={{ layout: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } }}
      className="rounded-xl border border-border/40 bg-card/80 shadow-lg backdrop-blur-sm transition-[border-color,box-shadow] focus-within:border-primary/50 focus-within:shadow-xl"
    >
      <PromptInput onSubmit={handleSubmit}>
        <CardSelectionChips />
        <PromptInputTextarea
          ref={textareaRef}
          placeholder={placeholderText}
          className="border-0 bg-transparent focus-visible:ring-0"
        />
        <PromptInputFooter>
          <div />
          <PromptInputSubmit
            disabled={isStreaming || hasPendingQuestions}
            className="bg-primary hover:bg-primary/90 active:scale-95 transition-transform"
          />
        </PromptInputFooter>
      </PromptInput>
    </motion.div>
  )

  // Which phase are the suggestion chips in?
  const suggestionsPhase = showAnalyzing
    ? 'skeleton' as const
    : showSuggestions
      ? 'ready' as const
      : null

  return (
    <LayoutGroup>
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* ── Empty state: centered hero ── */}
        <AnimatePresence>
          {isEmpty && (
            <motion.div
              key="empty-hero"
              className="flex flex-1 flex-col items-center justify-center px-4"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -24, transition: { duration: 0.25, ease: 'easeIn' } }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            >
              <div className="flex w-full max-w-2xl flex-col items-center gap-8">
                {/* Hero */}
                <div className="flex flex-col items-center gap-3">
                  <BrandLogo size="lg" animateOnMount expanded />
                  <AnimatePresence mode="wait">
                    <motion.p
                      key={showAnalyzing ? 'analyzing' : hasSources ? 'ready' : 'welcome'}
                      className="text-muted-foreground text-sm"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      {showAnalyzing
                        ? 'Analyzing your data...'
                        : hasSources
                          ? 'Your data is ready. What would you like to explore?'
                          : 'Upload data to analyze, or just ask me anything.'}
                    </motion.p>
                  </AnimatePresence>
                </div>

                {/* Suggestions / skeleton placeholders */}
                {suggestionsPhase && (
                  <div className="grid w-full grid-cols-1 gap-2 sm:grid-cols-2">
                    <AnimatePresence mode="popLayout">
                      {suggestionsPhase === 'skeleton'
                        ? Array.from({ length: 4 }, (_, i) => (
                            <motion.div
                              key={`skeleton-${i}`}
                              className="flex items-start gap-2.5 rounded-xl border border-border/30 px-4 py-3"
                              exit={{ opacity: 0, scale: 0.95 }}
                              transition={{ duration: 0.2, delay: i * 0.03 }}
                            >
                              <div className="mt-0.5 size-4 shrink-0 rounded skeleton-shimmer" />
                              <div className="flex flex-1 flex-col gap-1.5">
                                <div className="h-3.5 w-3/4 rounded skeleton-shimmer" />
                                <div className="h-3.5 w-1/2 rounded skeleton-shimmer" />
                              </div>
                            </motion.div>
                          ))
                        : suggestedQuestions.map((q, i) => (
                            <motion.button
                              key={`suggestion-${i}`}
                              type="button"
                              onClick={() => handleSuggestionClick(q)}
                              initial={wasAnalyzing ? { opacity: 0, y: 6 } : false}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.3, delay: wasAnalyzing ? i * 0.07 : 0 }}
                              className="group/chip flex items-start gap-2.5 rounded-xl border border-border/50 bg-card/60 px-4 py-3 text-left text-sm text-foreground backdrop-blur-sm transition-all hover:border-primary/30 hover:bg-card hover:shadow-md active:scale-[0.98]"
                            >
                              <Sparkles className="mt-0.5 size-4 shrink-0 text-accent transition-colors group-hover/chip:text-primary" />
                              <span>{q}</span>
                            </motion.button>
                          ))}
                    </AnimatePresence>
                  </div>
                )}

                {/* Prompt bar — centered position */}
                <div className="w-full">
                  {promptBar}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Conversation layout ── */}
        {!isEmpty && (
          <>
            <Conversation className="flex-1">
              <ConversationContent className="mx-auto max-w-3xl py-6">
                {isLoading && (
                  <div className="flex items-center justify-center py-16">
                    <PulsingDots />
                  </div>
                )}

                <AnimatePresence initial={false}>
                  {messages.map((msg) => (
                      <motion.div
                        key={msg.id}
                        variants={messageVariants}
                        initial={msg.role === 'user' ? 'hidden' : false}
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
                            </MessageContent>
                          ) : null}
                          {msg.has_figures && msg.figure_count > 0 && (
                            <MessageFigures
                              projectId={projectId}
                              chatId={resolvedChatId}
                              messageId={msg.backend_msg_id || msg.id}
                              figureCount={msg.figure_count}
                              code={msg.code}
                            />
                          )}
                          {msg.proposals && msg.proposals.length > 0 && (
                            <CardProposals
                              projectId={projectId}
                              chatId={resolvedChatId}
                              messageId={msg.backend_msg_id || msg.id}
                              proposals={msg.proposals}
                            />
                          )}
                          {msg.asked_questions && msg.asked_questions.length > 0 && (
                            <QuestionInput
                              questions={msg.asked_questions}
                              onSubmit={msg === lastMsg && hasPendingQuestions ? handleQuestionSubmit : undefined}
                            />
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
                          <MessageResponse className="streaming-cursor">
                            {streamingMessage.content}
                          </MessageResponse>
                        </MessageContent>
                      )}
                    </Message>
                  </motion.div>
                )}

              </ConversationContent>
              <ConversationScrollButton />
            </Conversation>

            {/* Prompt bar — bottom position */}
            <div className="px-4 pb-4">
              <div className="mx-auto max-w-3xl">
                {promptBar}
              </div>
            </div>
          </>
        )}
      </div>
    </LayoutGroup>
  )
}
