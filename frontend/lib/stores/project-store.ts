import { create } from 'zustand'

import type { ProjectSource } from '../api-types'

interface ProjectState {
  projectId: string | null
  name: string
  sources: ProjectSource[]
  suggestedQuestions: string[]
  isAnalyzing: boolean

  setProject: (projectId: string, name: string) => void
  setSources: (sources: ProjectSource[]) => void
  addSource: (source: ProjectSource) => void
  removeSource: (name: string) => void
  setSuggestedQuestions: (questions: string[]) => void
  setAnalyzing: (v: boolean) => void
  reset: () => void
}

const initialState = {
  projectId: null as string | null,
  name: '',
  sources: [] as ProjectSource[],
  suggestedQuestions: [] as string[],
  isAnalyzing: false,
}

export const useProjectStore = create<ProjectState>()((set) => ({
  ...initialState,

  setProject: (projectId, name) => set({
    projectId,
    name,
    sources: [],
    suggestedQuestions: [],
  }),

  setSources: (sources) => set({ sources }),

  addSource: (source) =>
    set((state) => ({ sources: [...state.sources, source] })),

  removeSource: (name) =>
    set((state) => ({ sources: state.sources.filter((s) => s.name !== name) })),

  setSuggestedQuestions: (questions) => set({ suggestedQuestions: questions }),
  setAnalyzing: (v) => set({ isAnalyzing: v }),
  reset: () => set(initialState),
}))
