'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { ReactGridLayout } from 'react-grid-layout/legacy'
import { GripVerticalIcon, PlusIcon, Trash2Icon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import CardEditor from './card-editor'
import type { DashboardCard, CardLayout } from '@/lib/domain-types'

import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'

const ROW_HEIGHT = 30
const GRID_MARGIN = 10
const HEADER_PX = 35
const COLS = 12

/** Convert a pixel height (content + header) to grid units. */
function pxToH(px: number): number {
  return Math.max(3, Math.ceil((px + GRID_MARGIN) / (ROW_HEIGHT + GRID_MARGIN)))
}

/** Minimum grid height per card type. */
function minH(type: DashboardCard['type']): number {
  if (type === 'chart') return 8
  if (type === 'metric') return 4
  return 3
}

/** Compute a default layout for a card when none is stored. */
function defaultLayout(card: DashboardCard, index: number): CardLayout {
  const w = 3
  const x = (index * w) % COLS
  if (card.type === 'metric') return { x, y: Infinity, w, h: 5 }
  if (card.type === 'note') return { x, y: Infinity, w, h: 4 }
  return { x, y: Infinity, w, h: 10 }
}

interface LayoutItem {
  i: string
  x: number
  y: number
  w: number
  h: number
  minW?: number
  minH?: number
}

/** Extract {id, layout} items from a react-grid-layout layout array. */
function layoutToItems(
  layout: readonly LayoutItem[],
): { id: string; layout: CardLayout }[] {
  return layout.map((l) => ({
    id: l.i,
    layout: { x: l.x, y: l.y, w: l.w, h: l.h },
  }))
}

interface DashboardGridProps {
  cards: DashboardCard[]
  onRemoveCard: (id: string) => void
  onAddNote: () => void
  onLayoutChange: (items: { id: string; layout: CardLayout }[]) => void
  onCardContentChange: (cardId: string, content: unknown[]) => void
}

export default function DashboardGrid({
  cards,
  onRemoveCard,
  onAddNote,
  onLayoutChange,
  onCardContentChange,
}: DashboardGridProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(1200)

  // Track cards and callback in refs so ResizeObserver/event handlers
  // always read fresh values without re-creating effects.
  const cardsRef = useRef(cards)
  cardsRef.current = cards
  const onLayoutChangeRef = useRef(onLayoutChange)
  onLayoutChangeRef.current = onLayoutChange

  // IDs of cards the user has manually shrunk below content height.
  const compactedRef = useRef(new Set<string>())

  // Trigger window resize after mount so Plotly charts recalculate dimensions
  useEffect(() => {
    const id = requestAnimationFrame(() => {
      window.dispatchEvent(new Event('resize'))
    })
    return () => cancelAnimationFrame(id)
  }, [])

  // Track container width
  useEffect(() => {
    if (!containerRef.current) return
    const observer = new ResizeObserver((entries) => {
      if (entries[0]) setWidth(entries[0].contentRect.width)
    })
    observer.observe(containerRef.current)
    return () => observer.disconnect()
  }, [])

  // --- Layout ---
  const layout: LayoutItem[] = cards.map((card, i) => {
    const l = card.layout ?? defaultLayout(card, i)
    return { i: card.id, x: l.x, y: l.y, w: l.w, h: l.h, minW: 2, minH: minH(card.type) }
  })

  // Persist layout on user drag stop
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleDragStop = useCallback((newLayout: any) => {
    onLayoutChange(layoutToItems(newLayout))
  }, [onLayoutChange])

  // Persist layout on user resize stop + track compaction
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleResizeStop = useCallback((newLayout: any, _oldItem: any, newItem: any) => {
    // If the user made the card shorter than its content, mark it compacted
    // so auto-height doesn't fight the user's choice.
    const contentEl = document.querySelector(`[data-card-id="${newItem.i}"]`) as HTMLElement | null
    if (contentEl && contentEl.scrollHeight > contentEl.clientHeight + 4) {
      compactedRef.current.add(newItem.i)
    } else {
      compactedRef.current.delete(newItem.i)
    }
    onLayoutChange(layoutToItems(newLayout))
  }, [onLayoutChange])

  // --- Auto-height: called by CardEditor when content size changes ---
  const handleEditorResize = useCallback((cardId: string, contentHeight: number) => {
    if (compactedRef.current.has(cardId)) return

    const currentCards = cardsRef.current
    const idx = currentCards.findIndex((c) => c.id === cardId)
    if (idx === -1) return

    const card = currentCards[idx]
    const l = card.layout ?? defaultLayout(card, idx)
    const neededH = Math.max(minH(card.type), pxToH(contentHeight + HEADER_PX))

    if (neededH !== l.h) {
      onLayoutChangeRef.current([{ id: cardId, layout: { ...l, h: neededH } }])
    }
  }, []) // stable: reads from refs

  return (
    <div ref={containerRef} className="h-full w-full">
      <div className="mb-4 flex justify-end">
        <Button variant="outline" size="sm" className="gap-2" onClick={onAddNote}>
          <PlusIcon className="size-4" />
          Add Note
        </Button>
      </div>

      <ReactGridLayout
        width={width}
        className="layout"
        layout={layout}
        cols={COLS}
        rowHeight={ROW_HEIGHT}
        draggableHandle=".drag-handle"
        onDragStop={handleDragStop}
        onResizeStop={handleResizeStop}
      >
        {cards.map((card) => (
          <div
            key={card.id}
            className="group flex flex-col overflow-hidden rounded-xl border border-border/50 bg-card shadow-sm transition-shadow hover:shadow-md"
          >
            <div className="drag-handle flex cursor-move items-center justify-between border-b border-border/40 bg-muted/30 px-3 py-1.5 opacity-50 transition-opacity group-hover:opacity-100">
              <div className="flex items-center gap-2 min-w-0">
                <GripVerticalIcon className="size-4 shrink-0 text-muted-foreground" />
                <h3 className="truncate text-sm font-medium text-foreground">{card.title}</h3>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 text-muted-foreground hover:text-destructive"
                onClick={() => onRemoveCard(card.id)}
              >
                <Trash2Icon className="h-3.5 w-3.5" />
              </Button>
            </div>

            <div data-card-id={card.id} className="flex-1 overflow-auto">
              <CardEditor
                card={card}
                onContentChange={onCardContentChange}
                onEditorResize={handleEditorResize}
              />
            </div>
          </div>
        ))}
      </ReactGridLayout>
    </div>
  )
}
