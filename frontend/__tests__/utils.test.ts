import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { cn, timeAgo } from '@/lib/utils'

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('px-2', 'py-1')).toBe('px-2 py-1')
  })

  it('resolves tailwind conflicts (last wins)', () => {
    expect(cn('px-2', 'px-4')).toBe('px-4')
  })

  it('handles conditional classes', () => {
    expect(cn('base', false && 'hidden', 'extra')).toBe('base extra')
  })

  it('returns empty string for no inputs', () => {
    expect(cn()).toBe('')
  })
})

describe('timeAgo', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-03-18T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns "just now" for < 60 seconds', () => {
    expect(timeAgo(new Date('2026-03-18T11:59:30Z'))).toBe('just now')
  })

  it('returns minutes ago', () => {
    expect(timeAgo(new Date('2026-03-18T11:55:00Z'))).toBe('5m ago')
  })

  it('returns hours ago', () => {
    expect(timeAgo(new Date('2026-03-18T09:00:00Z'))).toBe('3h ago')
  })

  it('returns days ago', () => {
    expect(timeAgo(new Date('2026-03-15T12:00:00Z'))).toBe('3d ago')
  })

  it('returns months ago', () => {
    expect(timeAgo(new Date('2025-12-18T12:00:00Z'))).toBe('3mo ago')
  })

  it('returns years ago', () => {
    expect(timeAgo(new Date('2024-01-01T00:00:00Z'))).toBe('2y ago')
  })

  it('accepts string dates', () => {
    expect(timeAgo('2026-03-18T11:50:00Z')).toBe('10m ago')
  })
})
