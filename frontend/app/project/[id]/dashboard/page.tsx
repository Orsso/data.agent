'use client'

import { useCallback, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { LayoutGridIcon, Loader2 } from 'lucide-react'
import Image from 'next/image'
import dynamic from 'next/dynamic'
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'

import { Button } from '@/components/ui/button'
import { useDashboardStore } from '@/lib/stores/dashboard-store'
import type { DashboardCard } from '@/lib/domain-types'

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
  const isGeneratingDashboard = useDashboardStore((s) => s.isGeneratingDashboard)
  const generateDashboard = useDashboardStore((s) => s.generateDashboard)

  useEffect(() => {
    if (projectId) {
      loadCards(projectId)
    }
  }, [projectId, loadCards])

  const handleGenerate = useCallback(() => {
    if (!projectId) return
    generateDashboard(projectId)
  }, [projectId, generateDashboard])

  return (
    <div className="flex-1 overflow-auto p-6">
      {dashboardCards.length === 0 ? (
        <div className="flex h-full flex-col items-center justify-center gap-6">
          <div className="flex flex-col items-center gap-4 text-center">
            {isGeneratingDashboard ? (
              <Image
                src="/icons/dashboard-building.svg"
                width={64}
                height={64}
                alt="Building dashboard..."
                className="opacity-90"
              />
            ) : (
              <div className="rounded-full bg-primary/10 p-4">
                <LayoutGridIcon className="h-10 w-10 text-primary" />
              </div>
            )}

            <div>
              <h2 className="text-xl font-semibold text-primary mb-2 font-everett">
                {isGeneratingDashboard ? 'Building Auto-Dashboard...' : 'Your Dashboard is empty'}
              </h2>
              <p className="text-muted-foreground max-w-sm">
                {isGeneratingDashboard
                  ? 'The AI is analyzing the dataset and picking the best charts and metrics. This usually takes around 30 seconds.'
                  : 'You can generate a starter dashboard automatically, or manually add your own custom charts from the Chat page.'}
              </p>
            </div>

            <div className="flex gap-4 mt-4">
              <Button
                size="lg"
                onClick={handleGenerate}
                disabled={isGeneratingDashboard}
                className="gap-2"
              >
                {isGeneratingDashboard ? (
                  <Loader2 className="animate-spin size-4" />
                ) : (
                  <LayoutGridIcon className="size-4" />
                )}
                {isGeneratingDashboard ? 'Generating...' : 'Auto-Generate Dashboard'}
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <DashboardGrid
          dashboardCards={dashboardCards}
          removeCard={(id) => removeCard(projectId, id)}
        />
      )}
    </div>
  )
}
