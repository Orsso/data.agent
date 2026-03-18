'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'next/navigation'
import { DownloadIcon, LayoutGridIcon, Loader2 } from 'lucide-react'
import Image from 'next/image'
import dynamic from 'next/dynamic'

import { Button } from '@/components/ui/button'
import { useDashboardStore } from '@/lib/stores/dashboard-store'
import { exportDashboardPdf } from '@/lib/export-dashboard-pdf'
import type { DashboardCard, CardLayout } from '@/lib/domain-types'
import type { DashboardGridHandle } from '@/components/dashboard/dashboard-grid'

const DashboardGrid = dynamic(
  () => import('@/components/dashboard/dashboard-grid'),
  { ssr: false }
)

const EMPTY_CARDS: DashboardCard[] = []

export default function ProjectDashboardPage() {
  const params = useParams()
  const projectId = params.id as string

  const dashboardCards = useDashboardStore((s) =>
    projectId ? s.dashboardCards[projectId] || EMPTY_CARDS : EMPTY_CARDS
  )
  const loadCards = useDashboardStore((s) => s.loadCards)
  const removeCard = useDashboardStore((s) => s.removeCard)
  const addNote = useDashboardStore((s) => s.addNote)
  const saveLayouts = useDashboardStore((s) => s.saveLayouts)
  const saveCardContent = useDashboardStore((s) => s.saveCardContent)
  const isGeneratingDashboard = useDashboardStore((s) => s.isGeneratingDashboard)
  const generateDashboard = useDashboardStore((s) => s.generateDashboard)

  const gridRef = useRef<DashboardGridHandle>(null)
  const [isExporting, setIsExporting] = useState(false)

  const handleExport = useCallback(async () => {
    const el = gridRef.current?.container
    if (!el) return
    setIsExporting(true)
    try {
      await exportDashboardPdf(el)
    } finally {
      setIsExporting(false)
    }
  }, [])

  useEffect(() => {
    if (projectId) loadCards(projectId)
  }, [projectId, loadCards])

  const handleGenerate = useCallback(() => {
    if (!projectId) return
    generateDashboard(projectId)
  }, [projectId, generateDashboard])

  const handleRemoveCard = useCallback(
    (id: string) => { if (projectId) removeCard(projectId, id) },
    [projectId, removeCard]
  )

  const handleAddNote = useCallback(() => {
    if (projectId) addNote(projectId)
  }, [projectId, addNote])

  const handleLayoutChange = useCallback(
    (items: { id: string; layout: CardLayout }[]) => {
      if (projectId) saveLayouts(projectId, items)
    },
    [projectId, saveLayouts]
  )

  const handleCardContentChange = useCallback(
    (cardId: string, content: unknown[]) => {
      if (projectId) saveCardContent(projectId, cardId, content)
    },
    [projectId, saveCardContent]
  )

  if (dashboardCards.length === 0 && !isGeneratingDashboard) {
    return (
      <div className="flex-1 overflow-auto bg-white p-6 dark:bg-card">
        <div className="flex h-full flex-col items-center justify-center gap-6">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="rounded-full bg-primary/10 p-4">
              <LayoutGridIcon className="h-10 w-10 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-primary mb-2 font-everett">
                Your Dashboard is empty
              </h2>
              <p className="text-muted-foreground max-w-sm">
                You can generate a starter dashboard automatically, or manually add your own custom charts from the Chat page.
              </p>
            </div>
            <div className="flex gap-4 mt-4">
              <Button size="lg" onClick={handleGenerate} className="gap-2">
                <LayoutGridIcon className="size-4" />
                Auto-Generate Dashboard
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-auto bg-white p-6 dark:bg-card">
      {isGeneratingDashboard && dashboardCards.length === 0 ? (
        <div className="flex h-full flex-col items-center justify-center gap-4">
          <Image
            src="/icons/dashboard-building.svg"
            width={64}
            height={64}
            alt="Building dashboard..."
            className="opacity-90"
          />
          <h2 className="text-xl font-semibold text-primary font-everett">
            Building Auto-Dashboard...
          </h2>
          <p className="text-muted-foreground max-w-sm text-center">
            The AI is analyzing the dataset and picking the best charts and metrics. This usually takes around 30 seconds.
          </p>
          <Loader2 className="animate-spin size-6 text-primary" />
        </div>
      ) : (
        <>
          <div className="mb-2 flex items-center justify-end">
            <button
              type="button"
              onClick={handleExport}
              disabled={isExporting}
              className="flex items-center gap-1.5 rounded-md border border-border/60 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
            >
              {isExporting
                ? <Loader2 className="size-3.5 animate-spin" />
                : <DownloadIcon className="size-3.5" />}
              Export PDF
            </button>
          </div>
          <DashboardGrid
            ref={gridRef}
            cards={dashboardCards}
            onRemoveCard={handleRemoveCard}
            onAddNote={handleAddNote}
            onLayoutChange={handleLayoutChange}
            onCardContentChange={handleCardContentChange}
          />
        </>
      )}
    </div>
  )
}
