import { describe, it, expect } from 'vitest'
import { TOOL_META, HIDDEN_TOOLS } from '@/lib/tool-meta'

describe('TOOL_META', () => {
  it('has active and done strings for each tool', () => {
    for (const [key, meta] of Object.entries(TOOL_META)) {
      expect(meta.active, `${key}.active`).toBeTruthy()
      expect(meta.done, `${key}.done`).toBeTruthy()
      expect(typeof meta.active).toBe('string')
      expect(typeof meta.done).toBe('string')
    }
  })

  it('contains the core tools', () => {
    expect(TOOL_META).toHaveProperty('execute_python')
    expect(TOOL_META).toHaveProperty('list_sources')
  })
})

describe('HIDDEN_TOOLS', () => {
  it('contains ask_question', () => {
    expect(HIDDEN_TOOLS.has('ask_question')).toBe(true)
  })

  it('every hidden tool has metadata', () => {
    for (const tool of HIDDEN_TOOLS) {
      expect(TOOL_META, `${tool} missing from TOOL_META`).toHaveProperty(tool)
    }
  })
})
