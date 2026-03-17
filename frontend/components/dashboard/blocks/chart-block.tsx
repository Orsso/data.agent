'use client'

import { useMemo } from 'react'
import { createReactBlockSpec } from '@blocknote/react'
import dynamic from 'next/dynamic'
import type * as Plotly from 'plotly.js'
import { cardRegistry } from './card-registry'

const Plot = dynamic(() => import('@/components/chat/plotly-lazy'), { ssr: false })

export const ChartBlock = createReactBlockSpec(
  {
    type: 'chart' as const,
    propSchema: {
      cardId: { default: '' },
    },
    content: 'none' as const,
  },
  {
    render: (props) => {
      const card = cardRegistry.get(props.block.props.cardId)

      // eslint-disable-next-line react-hooks/rules-of-hooks
      const { data, layout } = useMemo(() => {
        if (!card?.fig) return { data: [], layout: {} }

        const chartLayout: Partial<Plotly.Layout> = {
          ...(card.fig.layout as Partial<Plotly.Layout>),
          autosize: true,
          margin: { t: 30, r: 20, l: 40, b: 30 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { family: 'var(--font-sans)', color: 'currentColor' },
        }
        const d = (card.fig.data as Plotly.Data[]).map((trace) => ({ ...trace }))
        return { data: d, layout: chartLayout }
      }, [card?.fig])

      if (!card?.fig) {
        return (
          <div className="flex h-48 w-full items-center justify-center rounded-lg border border-dashed border-border/50 bg-muted/20 text-sm text-muted-foreground">
            No chart data
          </div>
        )
      }

      return (
        <div contentEditable={false} style={{ width: '100%', height: 300 }}>
          <Plot
            data={data}
            layout={layout}
            useResizeHandler
            style={{ width: '100%', height: '100%' }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>
      )
    },
  }
)
