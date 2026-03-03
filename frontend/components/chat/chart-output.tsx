'use client'

import { memo, useMemo } from 'react'
import dynamic from 'next/dynamic'
import { LayoutGridIcon } from 'lucide-react'
import type * as Plotly from 'plotly.js'
import { Button } from '@/components/ui/button'
import { useProjectStore } from '@/lib/stores/project-store'
import { useDashboardStore } from '@/lib/stores/dashboard-store'
import type { PlotlyFigure } from '@/lib/api-types'

const Plot = dynamic(() => import('./plotly-lazy'), {
  ssr: false,
  loading: () => (
    <div className="flex aspect-video w-full items-center justify-center rounded-xl border border-dashed border-border/50 bg-secondary/20">
      <div className="flex flex-col items-center gap-2 text-muted-foreground/60">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-r-transparent" />
        <span className="text-xs font-medium">Loading Chart...</span>
      </div>
    </div>
  ),
})

interface ChartOutputProps {
  figure: PlotlyFigure | string
  title?: string
  sourceAction?: boolean
}

function ChartOutputComponent({ figure, title, sourceAction = true }: ChartOutputProps) {
  const projectId = useProjectStore((s) => s.projectId)
  const addCard = useDashboardStore((s) => s.addCard)
  const divId = useMemo(() => `plotly-${crypto.randomUUID()}`, [])

  const parsedFigure = useMemo<PlotlyFigure>(() => {
    if (typeof figure === 'string') {
      try {
        return JSON.parse(figure) as PlotlyFigure
      } catch (err) {
        console.error('Failed to parse Plotly figure:', err)
        return { data: [], layout: {} }
      }
    }

    return figure
  }, [figure])

  const handleAddToDashboard = async () => {
    if (!projectId) return

    try {
      await addCard(projectId, {
        type: 'chart',
        title: title || 'Chart',
        fig: parsedFigure,
      })
    } catch (err) {
      console.error('Failed to add to dashboard:', err)
    }
  }

  const layout: Partial<Plotly.Layout> = {
    ...(parsedFigure.layout as Partial<Plotly.Layout>),
    autosize: true,
    margin: { t: 30, r: 20, l: 40, b: 30 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: {
      family: 'var(--font-sans)',
      color: 'currentColor',
    },
  }

  const data = parsedFigure.data.map((trace) => ({ ...trace })) as Plotly.Data[]

  return (
    <div className="flex w-full flex-col gap-2 rounded-xl border border-border/50 bg-card p-4 shadow-sm">
      {title && <h4 className="text-sm font-medium text-foreground">{title}</h4>}
      <div className="relative aspect-[16/9] w-full overflow-hidden">
        <Plot
          divId={divId}
          data={data}
          layout={layout}
          useResizeHandler
          style={{ width: '100%', height: '100%' }}
          config={{ displayModeBar: false, responsive: true }}
        />
      </div>

      {sourceAction && (
        <div className="mt-2 flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 gap-2 text-xs text-muted-foreground hover:text-foreground"
            onClick={handleAddToDashboard}
          >
            <LayoutGridIcon className="h-3.5 w-3.5" />
            Add to Dashboard
          </Button>
        </div>
      )}
    </div>
  )
}

export const ChartOutput = memo(ChartOutputComponent)
