import { create } from 'zustand'

import type { ProjectSummary } from '../api-types'
import { listProjects, deleteProject as apiDeleteProject } from '../backend-client'

interface ProjectsState {
  projects: ProjectSummary[]
  isLoading: boolean

  fetchProjects: () => Promise<void>
  deleteProject: (id: string) => Promise<void>
}

export const useProjectsStore = create<ProjectsState>()((set) => ({
  projects: [],
  isLoading: false,

  fetchProjects: async () => {
    set({ isLoading: true })
    try {
      const projects = await listProjects()
      set({ projects })
    } catch (err) {
      console.error('Failed to fetch projects:', err)
    } finally {
      set({ isLoading: false })
    }
  },

  deleteProject: async (id: string) => {
    await apiDeleteProject(id)
    set((state) => ({ projects: state.projects.filter((p) => p.id !== id) }))
  },
}))
