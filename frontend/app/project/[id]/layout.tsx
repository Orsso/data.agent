'use client'

import { useEffect, useCallback, useRef, useState, type KeyboardEvent } from 'react'
import Link from 'next/link'
import { useParams, usePathname, useRouter } from 'next/navigation'
import {
  DatabaseIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  LayoutGridIcon,
  MessageCircleIcon,
  Trash2Icon,
  UploadIcon,
  Loader2,
} from 'lucide-react'
import { BrandPlusIcon } from '@/components/icons/brand-plus'

import { BrandLogo } from '@/components/shared/brand-logo'
import { cn } from '@/lib/utils'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useProjectStore } from '@/lib/stores/project-store'
import { useChatsStore } from '@/lib/stores/chats-store'
import { useProjectBootstrap, useRunInsights } from '@/lib/hooks/use-project-bootstrap'
import { useUploadMessage } from '@/lib/hooks/use-upload-message'
import { addProjectSource, removeProjectSource, renameChat as apiRenameChat } from '@/lib/backend-client'
import { NEW_CHAT_ID } from '@/lib/constants'

export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  const params = useParams()
  const pathname = usePathname()
  const router = useRouter()
  const projectId = params.id as string

  const projectName = useProjectStore((s) => s.name)
  const sources = useProjectStore((s) => s.sources)
  const storeProjectId = useProjectStore((s) => s.projectId)
  const addSourceToStore = useProjectStore((s) => s.addSource)
  const removeSourceFromStore = useProjectStore((s) => s.removeSource)

  const chats = useChatsStore((s) => s.chats)
  const fetchChats = useChatsStore((s) => s.fetchChats)
  const deleteChat = useChatsStore((s) => s.deleteChat)
  const renameChatInStore = useChatsStore((s) => s.renameChat)

  const { loadProject } = useProjectBootstrap()
  const runInsights = useRunInsights()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const uploadMessage = useUploadMessage(isUploading)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [editingChatId, setEditingChatId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')

  useEffect(() => {
    if (storeProjectId !== projectId) {
      loadProject(projectId).catch(console.error)
    }
    fetchChats(projectId).catch(console.error)
  }, [projectId, storeProjectId, loadProject, fetchChats])

  useEffect(() => {
    document.title = projectName ? `data.agent | ${projectName}` : 'data.agent'
  }, [projectName, pathname])

  const handleStartRename = useCallback((chatId: string, currentTitle: string | null) => {
    setEditingChatId(chatId)
    setEditTitle(currentTitle || '')
  }, [])

  const handleConfirmRename = useCallback(async () => {
    if (!editingChatId) return
    const trimmed = editTitle.trim()
    if (trimmed) {
      renameChatInStore(editingChatId, trimmed)
      try {
        await apiRenameChat(projectId, editingChatId, trimmed)
      } catch (err) {
        console.error('Failed to rename chat:', err)
      }
    }
    setEditingChatId(null)
  }, [editingChatId, editTitle, projectId, renameChatInStore])

  const handleCancelRename = useCallback(() => {
    setEditingChatId(null)
  }, [])

  const handleRenameKeyDown = useCallback((e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleConfirmRename()
    else if (e.key === 'Escape') handleCancelRename()
  }, [handleConfirmRename, handleCancelRename])

  const handleDeleteChat = useCallback(
    async (e: React.MouseEvent, chatId: string) => {
      e.preventDefault()
      e.stopPropagation()
      try {
        await deleteChat(projectId, chatId)
        if (pathname.includes(`/chat/${chatId}`)) {
          router.push(`/project/${projectId}/chat/${NEW_CHAT_ID}`)
        }
      } catch (err) {
        console.error('Failed to delete chat:', err)
      }
    },
    [projectId, pathname, deleteChat, router]
  )

  const handleFileUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (!file) return
      setIsUploading(true)
      setUploadError(null)
      try {
        const source = await addProjectSource(projectId, file)
        addSourceToStore(source)
      } catch (err) {
        console.error('Upload failed:', err)
        setUploadError(err instanceof Error ? err.message : 'Upload failed')
        e.target.value = ''
        setIsUploading(false)
        return
      }
      setIsUploading(false)
      e.target.value = ''

      runInsights(projectId)
    },
    [projectId, addSourceToStore, runInsights]
  )

  const handleRemoveSource = useCallback(
    async (name: string) => {
      try {
        await removeProjectSource(projectId, name)
        removeSourceFromStore(name)
      } catch (err) {
        console.error('Failed to remove source:', err)
      }
    },
    [projectId, removeSourceFromStore]
  )

  const isDashboard = pathname.endsWith('/dashboard')

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-border/40 bg-card/80 px-4 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <BrandLogo href="/" />
          <div className="h-5 w-px bg-border/40" />
          <h1 className="text-base font-semibold text-foreground font-everett">{projectName || 'Project'}</h1>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="flex items-center gap-1.5 rounded-md border border-border/60 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            {isUploading ? <Loader2 className="size-3.5 animate-spin" /> : <UploadIcon className="size-3.5" />}
            Add CSV
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleFileUpload}
          />
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <DatabaseIcon className="size-3.5" />
            {sources.length} source{sources.length !== 1 ? 's' : ''}
          </span>
        </div>
      </header>

      {isUploading && (
        <div className="flex justify-end border-b border-primary/20 bg-primary/10 px-4 py-1.5 text-xs text-primary">
          {uploadMessage}
        </div>
      )}
      {uploadError && (
        <div className="flex items-center justify-between border-b border-destructive/20 bg-destructive/10 px-4 py-1.5 text-xs text-destructive">
          <span>{uploadError}</span>
          <button type="button" onClick={() => setUploadError(null)} className="ml-2 hover:underline">
            Dismiss
          </button>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className={cn(
          'flex shrink-0 flex-col border-r border-border/40 bg-card/50 transition-all duration-200',
          sidebarOpen ? 'w-56' : 'w-10'
        )}>
          {/* Toggle arrow */}
          <div className={cn('flex shrink-0 p-2', sidebarOpen ? 'justify-end' : 'justify-center')}>
            <button
              type="button"
              onClick={() => setSidebarOpen((v) => !v)}
              className="rounded-md p-1 text-muted-foreground transition-colors hover:text-foreground"
            >
              {sidebarOpen
                ? <ChevronLeftIcon className="size-3.5" />
                : <ChevronRightIcon className="size-3.5" />}
            </button>
          </div>

          {sidebarOpen ? (
            <div className="flex-1 overflow-auto px-3 pb-3">
              {/* Chats section */}
              <div className="mb-4">
                <span className="mb-2 block text-xs font-medium uppercase tracking-wider text-muted-foreground/60">
                  Chats
                </span>
                <div className="space-y-0.5">
                  {/* Permanent "New Chat" link */}
                  <Link
                    href={`/project/${projectId}/chat/${NEW_CHAT_ID}`}
                    className={cn(
                      'flex items-center gap-2 rounded-md px-2.5 py-1.5 text-sm transition-colors',
                      pathname.endsWith(`/chat/${NEW_CHAT_ID}`)
                        ? 'text-primary font-semibold'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    )}
                  >
                    <BrandPlusIcon className="size-3.5 shrink-0" />
                    <span>New Chat</span>
                  </Link>

                  {chats.map((chat) => {
                    const isActive =
                      pathname.includes(`/chat/${chat.id}`)
                    const isEditing = editingChatId === chat.id
                    return (
                      <Link
                        key={chat.id}
                        href={`/project/${projectId}/chat/${chat.id}`}
                        className={cn(
                          'group flex items-center justify-between rounded-md px-2.5 py-1.5 text-sm transition-colors',
                          isActive
                            ? 'text-primary font-semibold'
                            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                        )}
                      >
                        <span className="flex items-center gap-2 truncate min-w-0 flex-1">
                          <MessageCircleIcon className="size-3.5 shrink-0" />
                          {isEditing ? (
                            <input
                              type="text"
                              value={editTitle}
                              onChange={(e) => setEditTitle(e.target.value)}
                              onKeyDown={handleRenameKeyDown}
                              onBlur={handleConfirmRename}
                              onClick={(e) => e.preventDefault()}
                              autoFocus
                              className="w-full min-w-0 bg-transparent text-sm outline-none border-b border-primary/40"
                            />
                          ) : (
                            <span
                              className="truncate"
                              onDoubleClick={(e) => {
                                e.preventDefault()
                                handleStartRename(chat.id, chat.title)
                              }}
                            >
                              {chat.title || 'New chat'}
                            </span>
                          )}
                        </span>
                        {!isEditing && (
                          <button
                            type="button"
                            onClick={(e) => handleDeleteChat(e, chat.id)}
                            className="rounded p-0.5 opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                          >
                            <Trash2Icon className="size-3" />
                          </button>
                        )}
                      </Link>
                    )
                  })}
                </div>
              </div>

              {/* Dashboard link */}
              <div className="border-t border-border/30 pt-3">
                <Link
                  href={`/project/${projectId}/dashboard`}
                  className={cn(
                    'flex items-center gap-2 rounded-md px-2.5 py-1.5 text-sm transition-colors',
                    isDashboard
                      ? 'text-primary font-semibold'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  )}
                >
                  <LayoutGridIcon className="size-3.5" />
                  Dashboard
                </Link>
              </div>

              {/* Sources section */}
              {sources.length > 0 && (
                <div className="mt-4 border-t border-border/30 pt-3">
                  <span className="mb-2 block text-xs font-medium uppercase tracking-wider text-muted-foreground/60">
                    Sources
                  </span>
                  <TooltipProvider delayDuration={300}>
                    <div className="space-y-1">
                      {sources.map((src) => (
                        <Tooltip key={src.name}>
                          <TooltipTrigger asChild>
                            <div className="group flex items-center justify-between rounded-md px-2.5 py-1 text-xs text-muted-foreground">
                              <span className="flex items-center gap-1.5 truncate">
                                <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
                                {src.name}
                              </span>
                              <button
                                type="button"
                                onClick={() => handleRemoveSource(src.name)}
                                className="rounded p-0.5 opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                              >
                                <Trash2Icon className="size-3" />
                              </button>
                            </div>
                          </TooltipTrigger>
                          <TooltipContent side="right" className="max-w-xs">
                            <p className="font-medium">{src.name}</p>
                            <p className="text-primary-foreground/80">
                              {src.row_count.toLocaleString()} rows · {src.columns.length} columns
                            </p>
                            <p className="mt-1 text-primary-foreground/60">
                              {src.columns.slice(0, 8).join(', ')}
                              {src.columns.length > 8 && `, +${src.columns.length - 8} more`}
                            </p>
                          </TooltipContent>
                        </Tooltip>
                      ))}
                    </div>
                  </TooltipProvider>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-1">
              <Link
                href={`/project/${projectId}/chat/${NEW_CHAT_ID}`}
                className={cn(
                  'rounded-md p-2 transition-colors',
                  !isDashboard ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                )}
              >
                <MessageCircleIcon className="size-4" />
              </Link>
              <Link
                href={`/project/${projectId}/dashboard`}
                className={cn(
                  'rounded-md p-2 transition-colors',
                  isDashboard ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                )}
              >
                <LayoutGridIcon className="size-4" />
              </Link>
            </div>
          )}
        </aside>

        {/* Main content */}
        <main className="flex flex-1 flex-col overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  )
}
