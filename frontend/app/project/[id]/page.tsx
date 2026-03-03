'use client'

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { NEW_CHAT_ID } from '@/lib/constants'

/** Redirects /project/{id} → /project/{id}/chat/new */
export default function ProjectIndexPage() {
  const { id } = useParams()
  const router = useRouter()

  useEffect(() => {
    router.replace(`/project/${id}/chat/${NEW_CHAT_ID}`)
  }, [id, router])

  return null
}
