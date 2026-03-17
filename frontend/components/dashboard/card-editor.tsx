'use client'

import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  useCreateBlockNote,
  FormattingToolbarController,
  SuggestionMenuController,
  GridSuggestionMenuController,
  LinkToolbarController,
} from '@blocknote/react'
import { BlockNoteView } from '@blocknote/shadcn'
import '@blocknote/shadcn/style.css'

import { dashboardSchema } from './blocks/schema'
import { cardRegistry } from './blocks/card-registry'
import { portaledShadCNComponents } from './blocks/portaled-components'
import type { DashboardCard } from '@/lib/domain-types'

/** Default BlockNote content for a card based on its type. */
function defaultContent(card: DashboardCard): unknown[] {
  if (card.type === 'chart' && card.fig) {
    return [
      { type: 'chart', props: { cardId: card.id } },
      { type: 'paragraph', content: [] },
    ]
  }
  if (card.type === 'metric' && card.value) {
    return [
      { type: 'metric', props: { cardId: card.id } },
      { type: 'paragraph', content: [] },
    ]
  }
  return [{ type: 'paragraph', content: [] }]
}

/** Extract the editor document with a single type cast (BlockNote types are opaque). */
function getDoc(editor: { document: unknown }): unknown[] {
  return editor.document as unknown as unknown[]
}

/** Check whether the editor has any user-typed content (ignoring chart/metric atom blocks). */
function hasUserContent(blocks: unknown[]): boolean {
  for (const block of blocks) {
    const b = block as { type?: string; content?: unknown[] }
    if (b.type === 'chart' || b.type === 'metric') continue
    if (b.type === 'paragraph' && (!b.content || b.content.length === 0)) continue
    return true
  }
  return false
}

/**
 * Fixed positioning so floating-ui flip/shift middlewares resolve against the
 * viewport. Works because useCSSTransforms={false} on the grid removes the
 * CSS transform that would otherwise trap position:fixed inside the card.
 */
const FIXED_POSITIONING = { strategy: 'fixed' as const }

interface CardEditorProps {
  card: DashboardCard
  onContentChange: (cardId: string, content: unknown[]) => void
  /** Called when the editor's content height changes (for auto-height cards). */
  onEditorResize?: (cardId: string, contentHeight: number) => void
}

function CardEditor({ card, onContentChange, onEditorResize }: CardEditorProps) {
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const resizeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [isEmpty, setIsEmpty] = useState(true)
  const editorRef = useRef<{ document: unknown[] } | null>(null)
  const onContentChangeRef = useRef(onContentChange)
  onContentChangeRef.current = onContentChange
  const cardIdRef = useRef(card.id)
  cardIdRef.current = card.id

  // Keep the registry in sync with card data.
  useEffect(() => {
    cardRegistry.set(card.id, card)
    return () => { cardRegistry.delete(card.id) }
  }, [card.id, card.type, card.title, card.value, card.fig])

  const initialContent = useMemo(
    () => (card.content && card.content.length > 0 ? card.content : defaultContent(card)),
    // Only compute once per card ID
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [card.id]
  )

  const editor = useCreateBlockNote({
    schema: dashboardSchema,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    initialContent: initialContent as any,
  })
  editorRef.current = editor as unknown as { document: unknown[] }

  // Flush any pending debounced save when the component unmounts (e.g. tab switch).
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    return () => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current)
        saveTimerRef.current = null
        const doc = editorRef.current?.document
        if (doc) {
          onContentChangeRef.current(cardIdRef.current, doc)
        }
      }
    }
  }, [])

  /** Set initial isEmpty state + notify parent of initial height. */
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsEmpty(!hasUserContent(getDoc(editor)))
      const el = editor.domElement
      if (el && onEditorResize) onEditorResize(card.id, el.scrollHeight)
    }, 300)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleChange = useCallback(() => {
    // Track empty state for placeholder visibility
    setIsEmpty(!hasUserContent(getDoc(editor)))

    // Debounced content save
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
    saveTimerRef.current = setTimeout(() => {
      onContentChange(card.id, getDoc(editor))
    }, 1500)

    // Fast height notification for auto-resize
    if (onEditorResize) {
      if (resizeTimerRef.current) clearTimeout(resizeTimerRef.current)
      resizeTimerRef.current = setTimeout(() => {
        const el = editor.domElement
        if (el) onEditorResize(card.id, el.scrollHeight)
      }, 150)
    }
  }, [editor, card.id, onContentChange, onEditorResize])

  return (
    <div className={`card-editor ${isEmpty ? 'card-editor-empty' : ''}`}>
      <BlockNoteView
        editor={editor}
        onChange={handleChange}
        theme="light"
        sideMenu={false}
        formattingToolbar={false}
        linkToolbar={false}
        slashMenu={false}
        emojiPicker={false}
        shadCNComponents={portaledShadCNComponents}
      >
        <FormattingToolbarController floatingOptions={FIXED_POSITIONING} />
        <SuggestionMenuController triggerCharacter="/" floatingOptions={FIXED_POSITIONING} />
        <GridSuggestionMenuController
          triggerCharacter=":"
          columns={10}
          minQueryLength={2}
          floatingOptions={FIXED_POSITIONING}
        />
        <LinkToolbarController floatingOptions={FIXED_POSITIONING} />
      </BlockNoteView>
    </div>
  )
}

/**
 * Memoized to prevent re-renders when only the card layout changes
 * (e.g. after a drag/resize save updates card objects in the store).
 */
export default memo(CardEditor, (prev, next) => {
  return (
    prev.card.id === next.card.id &&
    prev.card.type === next.card.type &&
    prev.card.title === next.card.title &&
    prev.card.value === next.card.value &&
    prev.card.fig === next.card.fig &&
    prev.card.content === next.card.content &&
    prev.onContentChange === next.onContentChange &&
    prev.onEditorResize === next.onEditorResize
  )
})
