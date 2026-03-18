'use client'

import type { ComponentProps } from 'react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { ArrowDownIcon } from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import { StickToBottom, useStickToBottomContext } from 'use-stick-to-bottom'

export type ConversationProps = ComponentProps<typeof StickToBottom>

export const Conversation = ({ className, ...props }: ConversationProps) => (
  <StickToBottom
    className={cn('relative flex-1 overflow-y-hidden', className)}
    initial='smooth'
    resize='smooth'
    role='log'
    {...props}
  />
)

export type ConversationContentProps = ComponentProps<
  typeof StickToBottom.Content
>

export const ConversationContent = ({
  className,
  ...props
}: ConversationContentProps) => (
  <StickToBottom.Content
    className={cn('flex flex-col gap-8 p-4', className)}
    {...props}
  />
)

export type ConversationScrollButtonProps = ComponentProps<typeof Button>

export const ConversationScrollButton = ({
  className,
  ...props
}: ConversationScrollButtonProps) => {
  const { isAtBottom, scrollToBottom } = useStickToBottomContext()

  return (
    <AnimatePresence>
      {!isAtBottom && (
        <motion.div
          className="absolute bottom-4 left-1/2 z-10 -translate-x-1/2"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.2 }}
        >
          <Button
            className={cn(
              'rounded-full shadow-md dark:bg-background dark:hover:bg-muted',
              className
            )}
            onClick={() => scrollToBottom()}
            size='icon'
            type='button'
            variant='outline'
            {...props}
          >
            <ArrowDownIcon className='size-4' />
          </Button>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
