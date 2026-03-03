'use client'

import { useState, useEffect, useRef, memo } from 'react'
import { BrainIcon, ChevronDownIcon } from 'lucide-react'
import { Streamdown } from 'streamdown'

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'
import type { CotEntry } from '@/lib/domain-types'
import { TOOL_META, HIDDEN_TOOLS } from '@/lib/tool-meta'
import { ToolStepItem, ActiveTool } from './tool-step'

interface ThinkingBlockProps {
  cotEntries: CotEntry[]
  activeTool?: { name: string; args: string }
  isStreaming?: boolean
  thinkingDurationS?: number
  className?: string
}

function formatDuration(seconds: number): string {
  if (seconds < 1) return '<1s'
  return `${Math.round(seconds)}s`
}

function getStreamingLabel(
  hadThinking: boolean,
  toolCount: number,
  activeTool?: { name: string; args: string },
): string {
  if (activeTool) {
    return TOOL_META[activeTool.name]?.active || activeTool.name
  }
  const parts: string[] = []
  if (hadThinking) parts.push('Reasoning')
  if (toolCount) parts.push(`${toolCount} tool call${toolCount !== 1 ? 's' : ''}`)
  return parts.length ? parts.join(' \u00b7 ') : 'Thinking'
}

function getFinalLabel(
  hadThinking: boolean,
  toolCount: number,
  durationS?: number,
): string {
  const parts: string[] = []
  if (hadThinking) {
    parts.push(durationS != null ? `Thought for ${formatDuration(durationS)}` : 'Reasoning')
  }
  if (toolCount) {
    parts.push(`${toolCount} tool call${toolCount !== 1 ? 's' : ''}`)
  }
  return parts.length ? parts.join(' \u00b7 ') : 'Done'
}

const ThinkingMarkdown = memo(
  ({ children }: { children: string }) => (
    <Streamdown className="italic text-muted-foreground [&>*:first-child]:mt-0 [&>*:last-child]:mb-0" >
      {children}
    </Streamdown>
  ),
  (prev, next) => prev.children === next.children,
)
ThinkingMarkdown.displayName = 'ThinkingMarkdown'

/** Filter out hidden tools from CoT entries. */
function filterVisible(entries: CotEntry[]): CotEntry[] {
  return entries.filter(
    (e) => !(e.type === 'tool' && HIDDEN_TOOLS.has(e.step.tool_name)),
  )
}

export function ThinkingBlock({
  cotEntries,
  activeTool,
  isStreaming = false,
  thinkingDurationS,
  className,
}: ThinkingBlockProps) {
  const visibleEntries = filterVisible(cotEntries ?? [])
  const visibleActive = activeTool && !HIDDEN_TOOLS.has(activeTool.name) ? activeTool : undefined

  const hasContent = visibleEntries.length > 0 || !!visibleActive
  const hadThinking = visibleEntries.some((e) => e.type === 'thinking')
  const toolCount = visibleEntries.filter((e) => e.type === 'tool').length

  // Debounce visibility during streaming to prevent brief flash when the
  // model starts responding with text directly (no reasoning / tools).
  const showImmediately = !isStreaming && hasContent
  const [streamVisible, setStreamVisible] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    if (!isStreaming) {
      setStreamVisible(false) // eslint-disable-line react-hooks/set-state-in-effect -- intentional reset when streaming stops
      clearTimeout(timerRef.current)
      return
    }
    if (!hasContent) {
      clearTimeout(timerRef.current)
      return
    }
    timerRef.current = setTimeout(() => setStreamVisible(true), 200)
    return () => clearTimeout(timerRef.current)
  }, [isStreaming, hasContent])

  const visible = showImmediately || streamVisible

  // Never render when there's nothing to show
  if (!hasContent) return null
  // Still debouncing – don't mount the collapsible yet
  if (!visible) return null

  const label = isStreaming
    ? getStreamingLabel(hadThinking, toolCount, visibleActive)
    : getFinalLabel(hadThinking, toolCount, thinkingDurationS)

  return (
    <Collapsible defaultOpen={false} className={cn('mb-4', className)}>
      <div className="border-l-2 border-accent/40 pl-3">
        <CollapsibleTrigger className="flex w-full items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground">
          <BrainIcon className="size-4 text-accent" />
          <span className={cn('font-medium', isStreaming && 'animate-pulse')}>
            {label}
          </span>
          <ChevronDownIcon className="ml-auto size-4 transition-transform [[data-state=open]>&]:rotate-180" />
        </CollapsibleTrigger>

        <CollapsibleContent className="mt-3 space-y-3 text-sm">
          {visibleEntries.map((entry, i) =>
            entry.type === 'thinking' ? (
              <ThinkingMarkdown key={i}>{entry.content}</ThinkingMarkdown>
            ) : (
              <ToolStepItem key={i} step={entry.step} />
            ),
          )}
          {visibleActive && <ActiveTool name={visibleActive.name} args={visibleActive.args} />}
        </CollapsibleContent>
      </div>
    </Collapsible>
  )
}
