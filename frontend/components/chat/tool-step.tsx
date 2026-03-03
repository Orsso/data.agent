'use client'

import { CheckIcon, XIcon } from 'lucide-react'

import type { ToolStep as ToolStepType } from '@/lib/domain-types'
import { TOOL_META } from '@/lib/tool-meta'

interface ToolStepProps {
  step: ToolStepType
}

export function ToolStepItem({ step }: ToolStepProps) {
  const label = TOOL_META[step.tool_name]?.done || step.tool_name

  return (
    <div className="flex items-start gap-2 text-sm">
      {step.success ? (
        <CheckIcon className="mt-0.5 size-4 shrink-0 text-cobalt" />
      ) : (
        <XIcon className="mt-0.5 size-4 shrink-0 text-destructive" />
      )}
      <div className="min-w-0 flex-1">
        <span className="font-medium">{label}</span>
        <span className="text-muted-foreground"> — {step.summary}</span>
        <span className="text-muted-foreground/70 text-xs"> ({step.duration_ms}ms)</span>
      </div>
    </div>
  )
}

interface ActiveToolProps {
  name: string
  args: string
}

export function ActiveTool({ name, args }: ActiveToolProps) {
  const label = TOOL_META[name]?.active || name

  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <div className="size-4 animate-spin rounded-full border-2 border-sky border-t-transparent" />
      <span>{label}...</span>
      {args && <span className="truncate text-xs opacity-70">({args})</span>}
    </div>
  )
}
