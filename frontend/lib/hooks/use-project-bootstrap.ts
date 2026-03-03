import { useCallback } from 'react'

import {
  createProject,
  addProjectSource,
  runProjectInsights,
  getProject,
} from '../backend-client'
import { useProjectStore } from '../stores/project-store'

export function useRunInsights() {
  const setAnalyzing = useProjectStore((s) => s.setAnalyzing)
  const setSuggestedQuestions = useProjectStore((s) => s.setSuggestedQuestions)

  return useCallback(
    (projectId: string) => {
      setAnalyzing(true)
      runProjectInsights(projectId)
        .then((info) => {
          setSuggestedQuestions(info.suggested_questions)
        })
        .catch((err) => {
          console.error('Insights pipeline failed:', err)
        })
        .finally(() => {
          setAnalyzing(false)
        })
    },
    [setAnalyzing, setSuggestedQuestions]
  )
}

export function useProjectBootstrap() {
  const setProject = useProjectStore((s) => s.setProject)
  const setSources = useProjectStore((s) => s.setSources)
  const runInsights = useRunInsights()

  const createProjectWithUpload = useCallback(
    async (
      name: string,
      files?: File[],
      onPhase?: (phase: string) => void
    ): Promise<{ projectId: string }> => {
      onPhase?.('creating')
      const project = await createProject(name)
      setProject(project.id, project.name)

      if (files && files.length > 0) {
        onPhase?.('uploading')
        const sources = []
        for (const file of files) {
          const source = await addProjectSource(project.id, file)
          sources.push(source)
        }
        setSources(sources)
      }

      onPhase?.('done')

      if (files && files.length > 0) {
        runInsights(project.id)
      }

      return { projectId: project.id }
    },
    [setProject, setSources, runInsights]
  )

  const loadProject = useCallback(
    async (projectId: string) => {
      const info = await getProject(projectId)
      setProject(info.id, info.name)
      setSources(info.sources)
      useProjectStore.getState().setSuggestedQuestions(info.suggested_questions)
    },
    [setProject, setSources]
  )

  return { createProjectWithUpload, loadProject }
}
