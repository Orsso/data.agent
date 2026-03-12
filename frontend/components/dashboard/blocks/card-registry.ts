import type { DashboardCard } from '@/lib/domain-types'

/**
 * Module-level registry of card data, keyed by card ID.
 *
 * BlockNote renders custom blocks inside ProseMirror node views
 * which are isolated from the parent React tree. React Context
 * does not propagate. This registry provides a simple alternative:
 * - CardEditor populates it before mounting the editor.
 * - ChartBlock / MetricBlock read from it using a `cardId` prop.
 */
export const cardRegistry = new Map<string, DashboardCard>()
