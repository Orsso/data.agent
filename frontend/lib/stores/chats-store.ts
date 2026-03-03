import { create } from 'zustand'

import type { ChatSummary } from '../api-types'
import {
  listChats,
  createChat as apiCreateChat,
  deleteChat as apiDeleteChat,
} from '../backend-client'

interface ChatsState {
  chats: ChatSummary[]
  activeChatId: string | null

  fetchChats: (projectId: string) => Promise<void>
  createChat: (projectId: string, title?: string) => Promise<ChatSummary>
  deleteChat: (projectId: string, chatId: string) => Promise<void>
  renameChat: (chatId: string, title: string) => void
  setActiveChatId: (chatId: string | null) => void
  reset: () => void
}

export const useChatsStore = create<ChatsState>()((set) => ({
  chats: [],
  activeChatId: null,

  fetchChats: async (projectId: string) => {
    try {
      const chats = await listChats(projectId)
      set({ chats })
    } catch (err) {
      console.error('Failed to fetch chats:', err)
    }
  },

  createChat: async (projectId: string, title?: string) => {
    const chat = await apiCreateChat(projectId, title)
    set((state) => ({ chats: [chat, ...state.chats], activeChatId: chat.id }))
    return chat
  },

  deleteChat: async (projectId: string, chatId: string) => {
    await apiDeleteChat(projectId, chatId)
    set((state) => {
      const chats = state.chats.filter((c) => c.id !== chatId)
      const activeChatId =
        state.activeChatId === chatId ? (chats[0]?.id ?? null) : state.activeChatId
      return { chats, activeChatId }
    })
  },

  renameChat: (chatId, title) => set((state) => ({
    chats: state.chats.map((c) => c.id === chatId ? { ...c, title } : c),
  })),

  setActiveChatId: (chatId) => set({ activeChatId: chatId }),
  reset: () => set({ chats: [], activeChatId: null }),
}))
