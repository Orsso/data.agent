import { create } from 'zustand'
import {
  addDashboardCard,
  getProjectDashboardCards,
  removeDashboardCard,
  runProjectDashboard,
} from '../backend-client'

import type { PlotlyFigure, ProjectDashboardCard } from '../api-types'
import type { DashboardCard } from '../domain-types'

function toDashboardCard(card: ProjectDashboardCard): DashboardCard {
  return {
    id: card.id,
    type: card.type as DashboardCard['type'],
    title: card.title,
    code: card.code ?? undefined,
    value: card.value ?? undefined,
    fig: (card.fig as PlotlyFigure | null) ?? undefined,
    position: card.position,
  }
}

interface DashboardState {
  dashboardCards: Record<string, DashboardCard[]>
  isGeneratingDashboard: boolean

  loadCards: (projectId: string) => Promise<void>
  addCard: (projectId: string, card: Omit<DashboardCard, 'id' | 'position'> & { id?: string }) => Promise<void>
  removeCard: (projectId: string, id: string) => Promise<void>
  generateDashboard: (projectId: string) => Promise<void>
}

export const useDashboardStore = create<DashboardState>()((set) => ({
  dashboardCards: {},
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
      set((state) => {
        const projCards = state.dashboardCards[projectId] || []
        return {
          dashboardCards: {
            ...state.dashboardCards,
            [projectId]: [...projCards, toDashboardCard(saved)],
          },
        }
      })
    } catch (error) {
      console.error('Failed to add dashboard card:', error)
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
