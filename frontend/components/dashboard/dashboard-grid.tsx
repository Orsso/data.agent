'use client'

import { useEffect, useRef, useState } from 'react'
import { Responsive } from 'react-grid-layout/legacy'
import { Trash2Icon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ChartOutput } from '@/components/chat/chart-output'
import { useDashboardStore } from '@/lib/stores/dashboard-store'
import type { DashboardCard } from '@/lib/domain-types'

interface DashboardGridProps {
  dashboardCards: DashboardCard[]
  removeCard: (id: string) => void
}

export default function DashboardGrid({ dashboardCards, removeCard }: DashboardGridProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(1200)
  const selectedCardIds = useDashboardStore((s) => s.selectedCardIds)
  const toggleCardSelection = useDashboardStore((s) => s.toggleCardSelection)

  useEffect(() => {
    if (!containerRef.current) return

    const observer = new ResizeObserver((entries) => {
      if (entries[0]) {
        setWidth(entries[0].contentRect.width)
      }
    })

    observer.observe(containerRef.current)
    return () => observer.disconnect()
  }, [])

  return (
    <div ref={containerRef} className="h-full w-full">
      <Responsive
        width={width}
        className="layout"
        layouts={{
          lg: dashboardCards.map((card, i) => {
            const w = card.type === 'metric' ? 3 : 6
            const h = card.type === 'metric' ? 4 : 10
            return {
              i: card.id,
              x: (i * w) % 12,
              y: Infinity,
              w,
              h,
            }
          }),
        }}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
        rowHeight={30}
        draggableHandle=".drag-handle"
      >
        {dashboardCards.map((card) => {
          const isSelected = selectedCardIds.includes(card.id)
          return (
          <div
            key={card.id}
            className={`group flex flex-col overflow-hidden rounded-xl border bg-card shadow-sm transition-shadow hover:shadow-md ${
              isSelected ? 'border-primary ring-1 ring-primary/30' : 'border-border/50'
            }`}
          >
            <div className="drag-handle flex cursor-move items-center justify-between border-b border-border/40 bg-muted/30 px-4 py-2 opacity-50 transition-opacity group-hover:opacity-100">
              <div className="flex items-center gap-2 min-w-0">
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleCardSelection(card.id)}
                  onClick={(e) => e.stopPropagation()}
                  className="h-4 w-4 rounded border-border accent-primary cursor-pointer"
                />
                <h3 className="truncate font-medium text-foreground">{card.title}</h3>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 text-muted-foreground hover:text-destructive"
                onClick={() => removeCard(card.id)}
              >
                <Trash2Icon className="h-4 w-4" />
              </Button>
            </div>

            <div className="flex-1 overflow-auto p-4">
              {card.type === 'metric' ? (
                <div className="flex h-full items-center justify-center">
                  <p className="text-4xl font-semibold tracking-tight text-primary">{card.value}</p>
                </div>
              ) : (
                <div className="h-full w-full">
                  <ChartOutput figure={card.fig || { data: [], layout: {} }} sourceAction={false} />
                </div>
              )}
            </div>
          </div>
          )
        })}
      </Responsive>
    </div>
  )
}
