'use client'

import { useMemo } from 'react'
import { X } from 'lucide-react'

import { useDashboardStore } from '@/lib/stores/dashboard-store'
import { useProjectStore } from '@/lib/stores/project-store'

const EMPTY_CARDS: never[] = []

export function CardSelectionChips() {
  const projectId = useProjectStore((s) => s.projectId)
  const cards = useDashboardStore(
    (s) => (projectId && s.dashboardCards[projectId]) || EMPTY_CARDS,
  )
  const selectedCardIds = useDashboardStore((s) => s.selectedCardIds)
  const toggleCardSelection = useDashboardStore((s) => s.toggleCardSelection)

  const selectedCards = useMemo(
    () => cards.filter((c) => selectedCardIds.includes(c.id)),
    [cards, selectedCardIds],
  )

  if (selectedCards.length === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-1.5 px-3 pt-2">
      {selectedCards.map((card) => (
        <span
          key={card.id}
          className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary"
        >
          {card.title}
          <button
            type="button"
            onClick={() => toggleCardSelection(card.id)}
            className="ml-0.5 rounded-full p-0.5 hover:bg-primary/20"
          >
            <X className="h-3 w-3" />
          </button>
        </span>
      ))}
    </div>
  )
}
