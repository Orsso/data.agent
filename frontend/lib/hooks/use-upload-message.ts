import { useState, useEffect } from 'react'

const MESSAGES = [
  'Warming up the sandbox...',
  'Stretching our circuits...',
  'Polishing the algorithms...',
  'Waking up the hamsters...',
  'Syncing the quantum buffers...',
  'Calibrating the data sensors...',
  'Allocating extra brainpower...',
]

export function useUploadMessage(active: boolean) {
  const [idx, setIdx] = useState(0)

  useEffect(() => {
    if (!active) return
    setIdx(Math.floor(Math.random() * MESSAGES.length))
    const id = setInterval(() => {
      setIdx((prev) => {
        let next: number
        do { next = Math.floor(Math.random() * MESSAGES.length) } while (next === prev)
        return next
      })
    }, 3000)
    return () => clearInterval(id)
  }, [active])

  return MESSAGES[idx]
}
