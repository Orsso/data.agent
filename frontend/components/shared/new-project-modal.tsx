'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { UploadIcon, FileSpreadsheetIcon, XIcon } from 'lucide-react'

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Spinner } from '@/components/ui/spinner'
import { useProjectBootstrap } from '@/lib/hooks/use-project-bootstrap'
import { useUploadMessage } from '@/lib/hooks/use-upload-message'

type Phase = 'idle' | 'creating' | 'uploading' | 'done'

const PROGRESS_WIDTH: Record<Phase, string> = {
  idle: '0%',
  creating: '10%',
  uploading: '65%',
  done: '100%',
}

interface NewProjectModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated: (projectId: string) => void
}

export function NewProjectModal({
  open,
  onOpenChange,
  onCreated,
}: NewProjectModalProps) {
  const { createProjectWithUpload } = useProjectBootstrap()

  const [name, setName] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [phase, setPhase] = useState<Phase>('idle')
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const uploadMessage = useUploadMessage(phase === 'uploading')

  const fileInputRef = useRef<HTMLInputElement>(null)
  const busy = phase !== 'idle'

  // Reset state when modal closes
  useEffect(() => {
    if (!open) {
      setName('') // eslint-disable-line react-hooks/set-state-in-effect -- intentional reset when modal closes
      setFiles([])
      setPhase('idle')
      setError(null)
    }
  }, [open])

  const handleOpenChange = useCallback(
    (value: boolean) => {
      if (!value && busy) return // block close during creation
      onOpenChange(value)
    },
    [busy, onOpenChange]
  )

  const handleFilePick = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const picked = Array.from(e.target.files || []).filter((f) =>
        f.name.endsWith('.csv')
      )
      if (picked.length > 0) {
        setFiles((prev) => [...prev, ...picked])
      }
      e.target.value = ''
    },
    []
  )

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const dropped = Array.from(e.dataTransfer.files).filter((f) =>
      f.name.endsWith('.csv')
    )
    if (dropped.length > 0) {
      setFiles((prev) => [...prev, ...dropped])
    }
  }, [])

  const removeFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const handleCreate = useCallback(async () => {
    if (!name.trim()) return
    setError(null)

    try {
      const { projectId } = await createProjectWithUpload(
        name.trim(),
        files.length > 0 ? files : undefined,
        (p) => setPhase(p as Phase)
      )
      // Small delay so the user sees 100%
      await new Promise((r) => setTimeout(r, 400))
      onCreated(projectId)
    } catch (err) {
      setPhase('idle')
      setError(err instanceof Error ? err.message : 'Something went wrong')
    }
  }, [files, name, createProjectWithUpload, onCreated])

  const statusMessage =
    phase === 'creating'
      ? 'Setting up your project...'
      : phase === 'uploading'
        ? uploadMessage
        : phase === 'done'
          ? 'Done!'
          : null

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="sm:max-w-md"
        onPointerDownOutside={(e) => busy && e.preventDefault()}
        onEscapeKeyDown={(e) => busy && e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>New project</DialogTitle>
          <DialogDescription>
            Give your project a name. You can optionally upload CSV files to get started.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Project name */}
          <Input
            placeholder="e.g. Q4 Sales Analysis"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={busy}
            autoFocus
          />

          {/* File upload zone */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            multiple
            className="hidden"
            onChange={handleFilePick}
          />

          <button
            type="button"
            onClick={() => !busy && fileInputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            disabled={busy}
            className={`flex w-full flex-col items-center gap-2 rounded-lg border-2 border-dashed p-6 transition-colors ${
              isDragging
                ? 'border-primary/60 bg-primary/5'
                : files.length > 0
                  ? 'border-primary/40 bg-primary/[0.02]'
                  : 'border-border/60 hover:border-primary/30'
            } ${busy ? 'pointer-events-none opacity-60' : ''}`}
          >
            {files.length > 0 ? (
              <>
                <FileSpreadsheetIcon className="size-8 text-primary/70" />
                <span className="text-sm font-medium text-foreground">
                  {files.length} file{files.length !== 1 ? 's' : ''} selected
                </span>
                <span className="text-xs text-muted-foreground">
                  Click or drop to add more
                </span>
              </>
            ) : (
              <>
                <UploadIcon className="size-8 text-muted-foreground/50" />
                <span className="text-sm text-muted-foreground">
                  Drop CSV files here or click to browse (optional)
                </span>
              </>
            )}
          </button>

          {/* File list */}
          {files.length > 0 && !busy && (
            <div className="space-y-1">
              {files.map((f, i) => (
                <div
                  key={`${f.name}-${i}`}
                  className="flex items-center justify-between rounded-md bg-muted/50 px-3 py-1.5 text-sm"
                >
                  <span className="flex items-center gap-2 truncate">
                    <FileSpreadsheetIcon className="size-3.5 shrink-0 text-primary/70" />
                    <span className="truncate">{f.name}</span>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {(f.size / 1024).toFixed(0)} KB
                    </span>
                  </span>
                  <button
                    type="button"
                    onClick={() => removeFile(i)}
                    className="ml-2 rounded p-0.5 text-muted-foreground transition-colors hover:text-destructive"
                  >
                    <XIcon className="size-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Progress feedback */}
          {busy && (
            <div className="space-y-2">
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-700 ease-out"
                  style={{ width: PROGRESS_WIDTH[phase] }}
                />
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                {phase !== 'done' && <Spinner className="size-3.5" />}
                <span>{statusMessage}</span>
              </div>
            </div>
          )}

          {/* Error message */}
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={busy}
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            disabled={busy || !name.trim()}
          >
            {busy ? (
              <>
                <Spinner className="size-3.5" />
                Creating...
              </>
            ) : (
              'Create'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
