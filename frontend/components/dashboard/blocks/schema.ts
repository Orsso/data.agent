import { BlockNoteSchema, defaultBlockSpecs } from '@blocknote/core'
import { ChartBlock } from './chart-block'
import { MetricBlock } from './metric-block'

export const dashboardSchema = BlockNoteSchema.create({
  blockSpecs: {
    ...defaultBlockSpecs,
    chart: ChartBlock,
    metric: MetricBlock,
  },
})
