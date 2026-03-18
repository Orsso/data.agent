'use client'

import type { ComponentProps, HTMLAttributes } from 'react'

import { cn } from '@/lib/utils'
import { cjk } from '@streamdown/cjk'
import { code } from '@streamdown/code'
import { math } from '@streamdown/math'
import { mermaid } from '@streamdown/mermaid'
import { memo } from 'react'
import { Streamdown } from 'streamdown'

type MessageRole = 'user' | 'assistant'

export type MessageProps = HTMLAttributes<HTMLDivElement> & {
  from: MessageRole
}

export const Message = ({ className, from, ...props }: MessageProps) => (
  <div
    className={cn(
      'group flex w-full max-w-[95%] flex-col gap-2',
      from === 'user' ? 'is-user ml-auto justify-end' : 'is-assistant',
      className
    )}
    {...props}
  />
)

export type MessageContentProps = HTMLAttributes<HTMLDivElement>

export const MessageContent = ({
  children,
  className,
  ...props
}: MessageContentProps) => (
  <div
    className={cn(
      'flex w-fit min-w-0 max-w-full flex-col gap-2 overflow-hidden text-sm',
      'group-[.is-user]:ml-auto group-[.is-user]:rounded-2xl group-[.is-user]:bg-primary group-[.is-user]:px-4 group-[.is-user]:py-3 group-[.is-user]:text-primary-foreground',
      'group-[.is-assistant]:rounded-2xl group-[.is-assistant]:bg-card group-[.is-assistant]:px-4 group-[.is-assistant]:py-3 group-[.is-assistant]:text-foreground group-[.is-assistant]:shadow-sm',
      className
    )}
    {...props}
  >
    {children}
  </div>
)

export type MessageResponseProps = ComponentProps<typeof Streamdown>

const streamdownPlugins = { cjk, code, math, mermaid }

export const MessageResponse = memo(
  ({ className, ...props }: MessageResponseProps) => (
    <Streamdown
      className={cn(
        'prose-agent size-full',
        className
      )}
      plugins={streamdownPlugins}
      {...props}
    />
  ),
  (prevProps, nextProps) => prevProps.children === nextProps.children
)

MessageResponse.displayName = 'MessageResponse'
