'use client'

import { createReactBlockSpec } from '@blocknote/react'
import { cardRegistry } from './card-registry'

export const MetricBlock = createReactBlockSpec(
  {
    type: 'metric' as const,
    propSchema: {
      cardId: { default: '' },
    },
    content: 'none' as const,
  },
  {
    render: (props) => {
      const card = cardRegistry.get(props.block.props.cardId)

      if (!card) {
        return (
          <div className="flex h-24 w-full items-center justify-center rounded-lg border border-dashed border-border/50 bg-muted/20 text-sm text-muted-foreground">
            No metric data
          </div>
        )
      }

      return (
        <div contentEditable={false} className="flex flex-col items-center justify-center py-4">
          <p className="text-4xl font-semibold tracking-tight text-primary">{card.value}</p>
        </div>
      )
    },
  }
)
