'use client'

import { useMemo } from 'react'
import { BarChart3Icon, ChevronDownIcon, FileTextIcon, HashIcon, X } from 'lucide-react'

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { useDashboardStore } from '@/lib/stores/dashboard-store'
import { useProjectStore } from '@/lib/stores/project-store'
import type { DashboardCard } from '@/lib/domain-types'

const EMPTY_CARDS: never[] = []

const TYPE_ICON: Record<DashboardCard['type'], typeof BarChart3Icon> = {
  chart: BarChart3Icon,
  metric: HashIcon,
  note: FileTextIcon,
}

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
    <Collapsible className="px-3 pt-2">
      <CollapsibleTrigger className="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted/60">
        <span className="size-1.5 rounded-full bg-primary" />
        <span>{selectedCards.length} card{selectedCards.length > 1 ? 's' : ''} attached</span>
        <ChevronDownIcon className="size-3 transition-transform [[data-state=open]>&]:rotate-180" />
      </CollapsibleTrigger>

      <CollapsibleContent className="mt-1 flex flex-col gap-0.5 pl-1">
        {selectedCards.map((card) => {
          const Icon = TYPE_ICON[card.type]
          return (
            <div
              key={card.id}
              className="group/chip flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs text-muted-foreground hover:bg-muted/40"
            >
              <Icon className="size-3 shrink-0 text-muted-foreground/60" />
              <span className="truncate">{card.title}</span>
              <button
                type="button"
                onClick={() => toggleCardSelection(card.id)}
                className="ml-auto shrink-0 rounded p-0.5 text-muted-foreground/40 opacity-0 transition-opacity group-hover/chip:opacity-100 hover:text-foreground"
              >
                <X className="size-2.5" />
              </button>
            </div>
          )
        })}
      </CollapsibleContent>
    </Collapsible>
  )
}
