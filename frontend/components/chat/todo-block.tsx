'use client'

import { CheckCircle2Icon, ChevronDownIcon, CircleIcon, ListTodoIcon, LoaderIcon } from 'lucide-react'

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'
import type { TodoItem } from '@/lib/api-types'

interface TodoBlockProps {
  todos: TodoItem[]
  isStreaming?: boolean
  className?: string
}

const statusIcon: Record<TodoItem['status'], React.ReactNode> = {
  completed: <CheckCircle2Icon className="size-4 text-cobalt" />,
  in_progress: <LoaderIcon className="size-4 animate-spin text-amber-500" />,
  pending: <CircleIcon className="size-4 text-muted-foreground/50" />,
}

export function TodoBlock({ todos, isStreaming = false, className }: TodoBlockProps) {
  if (!todos.length) return null

  const completed = todos.filter((t) => t.status === 'completed').length
  const label = isStreaming
    ? `${completed}/${todos.length} tasks`
    : `${completed}/${todos.length} tasks completed`

  return (
    <Collapsible defaultOpen={isStreaming} className={cn('mb-4', className)}>
      <div className="border-l-2 border-accent/40 pl-3">
        <CollapsibleTrigger className="flex w-full items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground">
          <ListTodoIcon className="size-4 text-accent" />
          <span className={cn('font-medium', isStreaming && 'animate-pulse')}>
            {label}
          </span>
          <ChevronDownIcon className="ml-auto size-4 transition-transform [[data-state=open]>&]:rotate-180" />
        </CollapsibleTrigger>

        <CollapsibleContent className="mt-2 space-y-1">
          {todos.map((todo) => (
            <div key={todo.id} className="flex items-center gap-2 text-sm">
              <span className="mt-0.5 shrink-0">{statusIcon[todo.status]}</span>
              <span
                className={cn(
                  todo.status === 'completed' && 'text-muted-foreground line-through',
                  todo.status === 'in_progress' && 'text-foreground font-medium',
                  todo.status === 'pending' && 'text-muted-foreground',
                )}
              >
                {todo.content}
              </span>
            </div>
          ))}
        </CollapsibleContent>
      </div>
    </Collapsible>
  )
}
