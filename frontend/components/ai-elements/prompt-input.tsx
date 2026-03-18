'use client'

import {
  forwardRef,
  type ComponentProps,
  type FormEventHandler,
  type HTMLAttributes,
  type KeyboardEventHandler,
} from 'react'

import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from '@/components/ui/input-group'
import { cn } from '@/lib/utils'
import { ArrowSubmitIcon } from '@/components/icons/arrow-submit'
import { useCallback, useRef, useState } from 'react'

export interface PromptInputMessage {
  text: string
}

export type PromptInputProps = Omit<
  HTMLAttributes<HTMLFormElement>,
  'onSubmit'
> & {
  onSubmit: (
    message: PromptInputMessage,
    event: React.FormEvent<HTMLFormElement>
  ) => void | Promise<void>
}

export const PromptInput = ({
  className,
  onSubmit,
  children,
  ...props
}: PromptInputProps) => {
  const formRef = useRef<HTMLFormElement | null>(null)

  const handleSubmit: FormEventHandler<HTMLFormElement> = useCallback(
    async (event) => {
      event.preventDefault()

      const form = event.currentTarget
      const formData = new FormData(form)
      const text = (formData.get('message') as string) || ''

      form.reset()

      try {
        const result = onSubmit({ text }, event)
        if (result instanceof Promise) {
          await result
        }
      } catch {
        // Swallow — caller handles errors
      }
    },
    [onSubmit]
  )

  return (
    <form
      className={cn('w-full', className)}
      onSubmit={handleSubmit}
      ref={formRef}
      {...props}
    >
      <InputGroup className='overflow-hidden border-0 shadow-none ring-0!'>{children}</InputGroup>
    </form>
  )
}

export type PromptInputTextareaProps = ComponentProps<
  typeof InputGroupTextarea
>

export const PromptInputTextarea = forwardRef<
  HTMLTextAreaElement,
  PromptInputTextareaProps
>(({
  onChange,
  onKeyDown,
  className,
  placeholder = 'What would you like to know?',
  ...props
}, ref) => {
  const [isComposing, setIsComposing] = useState(false)

  const handleKeyDown: KeyboardEventHandler<HTMLTextAreaElement> = useCallback(
    (e) => {
      onKeyDown?.(e)

      if (e.defaultPrevented) {
        return
      }

      if (e.key === 'Enter') {
        if (isComposing || e.nativeEvent.isComposing) {
          return
        }
        if (e.shiftKey) {
          return
        }

        const { form } = e.currentTarget
        const submitButton = form?.querySelector(
          'button[type="submit"]'
        ) as HTMLButtonElement | null
        if (submitButton?.disabled) {
          return
        }

        e.preventDefault()
        form?.requestSubmit()
      }
    },
    [onKeyDown, isComposing]
  )

  const handleCompositionEnd = useCallback(() => setIsComposing(false), [])
  const handleCompositionStart = useCallback(() => setIsComposing(true), [])

  return (
    <InputGroupTextarea
      ref={ref}
      className={cn('field-sizing-content max-h-48 min-h-16', className)}
      name='message'
      onChange={onChange}
      onCompositionEnd={handleCompositionEnd}
      onCompositionStart={handleCompositionStart}
      onKeyDown={handleKeyDown}
      placeholder={placeholder}
      {...props}
    />
  )
})
PromptInputTextarea.displayName = 'PromptInputTextarea'

export type PromptInputFooterProps = Omit<
  ComponentProps<typeof InputGroupAddon>,
  'align'
>

export const PromptInputFooter = ({
  className,
  ...props
}: PromptInputFooterProps) => (
  <InputGroupAddon
    align='block-end'
    className={cn('justify-between gap-1', className)}
    {...props}
  />
)

export type PromptInputSubmitProps = ComponentProps<typeof InputGroupButton>

export const PromptInputSubmit = ({
  className,
  variant = 'default',
  size = 'icon-sm',
  children,
  ...props
}: PromptInputSubmitProps) => {
  return (
    <InputGroupButton
      aria-label='Submit'
      className={cn('size-9 rounded-full bg-primary text-primary-foreground hover:bg-primary/90', className)}
      size={size}
      type='submit'
      variant={variant}
      {...props}
    >
      {children ?? <ArrowSubmitIcon className='size-5' />}
    </InputGroupButton>
  )
}
