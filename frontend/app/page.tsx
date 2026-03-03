'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  DatabaseIcon,
  FolderIcon,
  MessageCircleIcon,
  PlusIcon,
  Trash2Icon,
} from 'lucide-react'

import { useProjectsStore } from '@/lib/stores/projects-store'
import { NEW_CHAT_ID } from '@/lib/constants'
import { NewProjectModal } from '@/components/shared/new-project-modal'
import { BrandLogo } from '@/components/shared/brand-logo'
import { timeAgo } from '@/lib/utils'
import type { ProjectSummary } from '@/lib/api-types'

export default function HomePage() {
  const router = useRouter()

  const projects = useProjectsStore((s) => s.projects)
  const isLoading = useProjectsStore((s) => s.isLoading)
  const fetchProjects = useProjectsStore((s) => s.fetchProjects)
  const deleteProject = useProjectsStore((s) => s.deleteProject)

  const [modalOpen, setModalOpen] = useState(false)

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  const handleCreated = useCallback(
    (projectId: string) => {
      setModalOpen(false)
      router.push(`/project/${projectId}/chat/${NEW_CHAT_ID}`)
    },
    [router]
  )

  const handleDeleteProject = useCallback(
    async (e: React.MouseEvent, id: string) => {
      e.stopPropagation()
      try {
        await deleteProject(id)
      } catch (err) {
        console.error('Failed to delete project:', err)
      }
    },
    [deleteProject]
  )

  const stats = useMemo(() => ({
    projects: projects.length,
    sources: projects.reduce((sum, p) => sum + p.source_count, 0),
    chats: projects.reduce((sum, p) => sum + p.chat_count, 0),
  }), [projects])

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-5xl">
        {/* Hero */}
        <div className="mb-10 flex items-start justify-between">
          <div>
            <BrandLogo size="lg" expanded animateOnMount />
            <p className="mt-3 text-sm text-muted-foreground">
              Your data analysis projects
            </p>
          </div>
          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            <PlusIcon className="size-4" />
            New Project
          </button>
        </div>

        <NewProjectModal
          open={modalOpen}
          onOpenChange={setModalOpen}
          onCreated={handleCreated}
        />

        {/* Stats */}
        {projects.length > 0 && (
          <div className="mb-6 flex items-center gap-6 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <FolderIcon className="size-3.5" />
              {stats.projects} project{stats.projects !== 1 ? 's' : ''}
            </span>
            <span className="flex items-center gap-1.5">
              <DatabaseIcon className="size-3.5" />
              {stats.sources} source{stats.sources !== 1 ? 's' : ''}
            </span>
            <span className="flex items-center gap-1.5">
              <MessageCircleIcon className="size-3.5" />
              {stats.chats} chat{stats.chats !== 1 ? 's' : ''}
            </span>
          </div>
        )}

        {/* Grid */}
        {projects.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onClick={() => router.push(`/project/${project.id}`)}
                onDelete={(e) => handleDeleteProject(e, project.id)}
              />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && projects.length === 0 && (
          <div className="mt-24 flex flex-col items-center text-center">
            <DatabaseIcon className="size-10 text-muted-foreground/30" />
            <p className="mt-4 text-sm text-muted-foreground">
              No projects yet
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function ProjectCard({
  project,
  onClick,
  onDelete,
}: {
  project: ProjectSummary
  onClick: () => void
  onDelete: (e: React.MouseEvent) => void
}) {
  const MAX_TAGS = 2
  const visibleSources = project.source_names.slice(0, MAX_TAGS)
  const remaining = project.source_names.length - MAX_TAGS

  return (
    <button
      type="button"
      onClick={onClick}
      className="group relative flex flex-col rounded-xl border border-border/50 bg-card p-5 text-left shadow-sm transition-all hover:border-primary/30 hover:shadow-md min-h-[180px]"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <div className="size-2 shrink-0 rounded-full bg-emerald-500" />
          <h3 className="text-base font-semibold text-foreground line-clamp-1">
            {project.name}
          </h3>
        </div>
        <button
          type="button"
          onClick={onDelete}
          className="rounded-md p-1 text-muted-foreground/40 opacity-0 transition-all hover:text-destructive group-hover:opacity-100"
        >
          <Trash2Icon className="size-3.5" />
        </button>
      </div>

      {project.source_names.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {visibleSources.map((name) => (
            <span
              key={name}
              className="inline-flex items-center rounded-md bg-muted/60 px-2 py-0.5 text-xs text-muted-foreground"
            >
              {name}
            </span>
          ))}
          {remaining > 0 && (
            <span className="inline-flex items-center rounded-md bg-muted/40 px-2 py-0.5 text-xs text-muted-foreground/70">
              +{remaining} more
            </span>
          )}
        </div>
      )}

      <div className="mt-auto flex items-center gap-4 pt-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <DatabaseIcon className="size-3.5" />
          {project.source_count} source{project.source_count !== 1 ? 's' : ''}
        </span>
        <span className="flex items-center gap-1">
          <MessageCircleIcon className="size-3.5" />
          {project.chat_count} chat{project.chat_count !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="mt-2 text-xs text-muted-foreground/50">
        {timeAgo(project.updated_at)}
      </div>
    </button>
  )
}
