'use client'

import { useEffect, useState } from 'react'
import { getProjectMessageFigures } from '@/lib/backend-client'
import { NEW_CHAT_ID } from '@/lib/constants'
import type { PlotlyFigure } from '@/lib/api-types'
import { ChartOutput } from './chart-output'

interface MessageFiguresProps {
  projectId: string
  chatId: string
  messageId: string
  figureCount: number
  code?: string
}

export function MessageFigures({ projectId, chatId, messageId, figureCount, code }: MessageFiguresProps) {
  const [figures, setFigures] = useState<PlotlyFigure[]>([])
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if (figureCount <= 0 || chatId === NEW_CHAT_ID) return

    let mounted = true

    getProjectMessageFigures(projectId, chatId, messageId)
      .then((data) => {
        if (!mounted) return
        setFigures(data)
        setLoaded(true)
      })
      .catch((err) => {
        console.error('Failed to load figures:', err)
        if (mounted) setLoaded(true)
      })

    return () => {
      mounted = false
    }
  }, [projectId, chatId, messageId, figureCount])

  if (figureCount <= 0) return null

  if (!loaded) {
    return (
      <div className="mt-4 flex w-full flex-col gap-4">
        {Array.from({ length: figureCount }).map((_, i) => (
          <div
            key={i}
            className="flex aspect-[16/9] w-full animate-pulse flex-col items-center justify-center rounded-xl border border-dashed border-border/50 bg-secondary/10"
          >
            <span className="text-xs text-muted-foreground">Loading chart...</span>
          </div>
        ))}
      </div>
    )
  }

  if (figures.length === 0) return null

  return (
    <div className="mt-4 flex w-full flex-col gap-4">
      {figures.map((fig, i) => (
        <ChartOutput key={i} figure={fig} code={code} />
      ))}
    </div>
  )
}
