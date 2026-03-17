import { create } from 'zustand'
import {
  addDashboardCard,
  getProjectDashboardCards,
  removeDashboardCard,
  runProjectDashboard,
  updateDashboardCard,
  updateDashboardLayouts,
} from '../backend-client'

import type { PlotlyFigure, ProjectDashboardCard } from '../api-types'
import type { CardLayout, DashboardCard } from '../domain-types'

function toDashboardCard(card: ProjectDashboardCard): DashboardCard {
  return {
    id: card.id,
    type: card.type as DashboardCard['type'],
    title: card.title,
    code: card.code ?? undefined,
    value: card.value ?? undefined,
    fig: (card.fig as PlotlyFigure | null) ?? undefined,
    content: card.content ?? undefined,
    layout: card.layout as CardLayout | undefined,
    position: card.position,
  }
}

interface DashboardState {
  dashboardCards: Record<string, DashboardCard[]>
  selectedCardIds: string[]
  isGeneratingDashboard: boolean

  loadCards: (projectId: string) => Promise<void>
  addCard: (projectId: string, card: Omit<DashboardCard, 'id' | 'position'> & { id?: string }) => Promise<void>
  addNote: (projectId: string) => Promise<void>
  removeCard: (projectId: string, id: string) => Promise<void>
  saveLayouts: (projectId: string, items: { id: string; layout: CardLayout }[]) => Promise<void>
  saveCardContent: (projectId: string, cardId: string, content: unknown[]) => Promise<void>
  generateDashboard: (projectId: string) => Promise<void>
  toggleCardSelection: (cardId: string) => void
  clearSelection: () => void
}

/** Append a newly-created card to a project's list in the store. */
function appendCard(
  set: (fn: (state: DashboardState) => Partial<DashboardState>) => void,
  projectId: string,
  saved: ProjectDashboardCard,
) {
  set((state) => {
    const projCards = state.dashboardCards[projectId] || []
    return {
      dashboardCards: {
        ...state.dashboardCards,
        [projectId]: [...projCards, toDashboardCard(saved)],
      },
    }
  })
}

export const useDashboardStore = create<DashboardState>()((set) => ({
  dashboardCards: {},
  selectedCardIds: [] as string[],
  isGeneratingDashboard: false,

  loadCards: async (projectId) => {
    try {
      const cards = await getProjectDashboardCards(projectId)
      set((state) => ({
        dashboardCards: {
          ...state.dashboardCards,
          [projectId]: cards.map(toDashboardCard),
        },
      }))
    } catch (error) {
      console.error('Failed to load dashboard cards:', error)
    }
  },

  addCard: async (projectId, card) => {
    try {
      const saved = await addDashboardCard(projectId, {
        type: card.type,
        title: card.title,
        code: card.code,
        value: card.value,
        fig: card.fig as Record<string, unknown> | null,
      })
      appendCard(set, projectId, saved)
    } catch (error) {
      console.error('Failed to add dashboard card:', error)
    }
  },

  addNote: async (projectId) => {
    try {
      const saved = await addDashboardCard(projectId, { type: 'note', title: 'Note' })
      appendCard(set, projectId, saved)
    } catch (error) {
      console.error('Failed to add note card:', error)
    }
  },

  removeCard: async (projectId, id) => {
    try {
      await removeDashboardCard(projectId, id)
      set((state) => {
        const projCards = state.dashboardCards[projectId] || []
        return {
          dashboardCards: {
            ...state.dashboardCards,
            [projectId]: projCards.filter((c) => c.id !== id),
          },
        }
      })
    } catch (error) {
      console.error('Failed to remove dashboard card:', error)
    }
  },

  saveLayouts: async (projectId, items) => {
    // Optimistic update — apply layout changes immediately so the grid
    // re-renders without waiting for the API round-trip.
    set((state) => {
      const projCards = state.dashboardCards[projectId] || []
      const layoutMap = new Map(items.map((i) => [i.id, i.layout]))
      let changed = false
      const next = projCards.map((c) => {
        const layout = layoutMap.get(c.id)
        if (!layout) return c
        const prev = c.layout
        if (
          prev &&
          prev.x === layout.x &&
          prev.y === layout.y &&
          prev.w === layout.w &&
          prev.h === layout.h
        ) {
          return c // identical — keep same reference
        }
        changed = true
        return { ...c, layout }
      })
      if (!changed) return state // no store update at all
      return {
        dashboardCards: {
          ...state.dashboardCards,
          [projectId]: next,
        },
      }
    })
    try {
      await updateDashboardLayouts(projectId, items)
    } catch (error) {
      console.error('Failed to save layouts:', error)
    }
  },

  saveCardContent: async (projectId, cardId, content) => {
    // Optimistic update — keep local state in sync so navigating away
    // and back shows the latest content even before the API responds.
    set((state) => {
      const projCards = state.dashboardCards[projectId]
      if (!projCards) return state
      const idx = projCards.findIndex((c) => c.id === cardId)
      if (idx === -1) return state
      const card = projCards[idx]
      if (card.content === content) return state
      const next = [...projCards]
      next[idx] = { ...card, content }
      return { dashboardCards: { ...state.dashboardCards, [projectId]: next } }
    })
    try {
      await updateDashboardCard(projectId, cardId, { content })
    } catch (error) {
      console.error('Failed to save card content:', error)
    }
  },

  toggleCardSelection: (cardId) => set((state) => ({
    selectedCardIds: state.selectedCardIds.includes(cardId)
      ? state.selectedCardIds.filter((id) => id !== cardId)
      : [...state.selectedCardIds, cardId],
  })),

  clearSelection: () => set((state) =>
    state.selectedCardIds.length === 0 ? state : { selectedCardIds: [] }
  ),

  generateDashboard: async (projectId) => {
    set({ isGeneratingDashboard: true })
    try {
      const cards = await runProjectDashboard(projectId)
      set((state) => ({
        dashboardCards: {
          ...state.dashboardCards,
          [projectId]: cards.map(toDashboardCard),
        },
      }))
    } catch (error) {
      console.error('Failed to generate dashboard:', error)
    } finally {
      set({ isGeneratingDashboard: false })
    }
  },
}))
