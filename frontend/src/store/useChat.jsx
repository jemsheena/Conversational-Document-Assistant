import { useEffect, useState } from 'react'
import { chatStream, ingestDocuments } from '../api/client'

const LEGACY_DEFAULT_COLLECTION = 'default'
const NEW_CONV_TITLE = 'New conversation'
const STORAGE_KEY = 'chat_state_v2'

function newConversationId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function collectionForConversation(conv) {
  const id = conv?.id || newConversationId()
  if (!conv?.collection || conv.collection === LEGACY_DEFAULT_COLLECTION) {
    return id
  }
  return conv.collection
}

function createConversation() {
  const id = newConversationId()
  return {
    id,
    title: NEW_CONV_TITLE,
    pinned: false,
    collection: id,
    messages: [],
    uploadedFiles: [],
    hasDocuments: false,
    lastUpload: null,
  }
}

function normalizeConversation(conv) {
  const id = conv?.id || newConversationId()
  return {
    id,
    title: conv?.title || NEW_CONV_TITLE,
    pinned: Boolean(conv?.pinned),
    collection: collectionForConversation({ ...conv, id }),
    messages: Array.isArray(conv?.messages) ? conv.messages : [],
    uploadedFiles: Array.isArray(conv?.uploadedFiles) ? conv.uploadedFiles : [],
    hasDocuments: Boolean(conv?.hasDocuments),
    lastUpload: conv?.lastUpload || null,
  }
}

function loadPersistedState() {
  const keys = [STORAGE_KEY, 'chat_state_v1']
  for (const key of keys) {
    try {
      const raw = localStorage.getItem(key)
      if (!raw) continue
      const parsed = JSON.parse(raw)
      const loadedConversations = Array.isArray(parsed?.conversations)
        ? parsed.conversations.map(normalizeConversation)
        : []
      if (loadedConversations.length === 0) continue
      const activeConvId =
        loadedConversations.find((conv) => conv.id === parsed?.activeConvId)?.id ??
        loadedConversations[0].id
      return { conversations: loadedConversations, activeConvId }
    } catch {
      continue
    }
  }
  return null
}

function loadInitialState() {
  const persisted = loadPersistedState()
  if (persisted) return persisted
  const initial = createConversation()
  return { conversations: [initial], activeConvId: initial.id }
}

export function useChat() {
  const [initialState] = useState(loadInitialState)
  const [conversations, setConversations] = useState(initialState.conversations)
  const [activeConvId, setActiveConvId] = useState(initialState.activeConvId)
  const [isLoading, setIsLoading] = useState(false)
  const [streamingResponses, setStreamingResponses] = useState({})
  const [isUploading, setIsUploading] = useState(false)

  const activeConversation = conversations.find((conv) => conv.id === activeConvId) ?? null
  const messages = activeConversation?.messages ?? []
  const currentResponse = activeConvId ? streamingResponses[activeConvId] || '' : ''

  const updateActiveConversation = (updater) => {
    setConversations((prev) =>
      prev.map((conv) => (conv.id === activeConvId ? updater(conv) : conv))
    )
  }

  const createNewChat = () => {
    const next = createConversation()
    setConversations((prev) => [next, ...prev])
    setActiveConvId(next.id)
    return next.id
  }

  const selectConversation = (id) => {
    setActiveConvId(id)
  }

  const setActiveCollection = (collection) => {
    if (!collection) return
    updateActiveConversation((conv) => ({ ...conv, collection }))
  }

  const renameConversation = (id, title) => {
    const nextTitle = title?.trim()
    if (!nextTitle) return
    setConversations((prev) =>
      prev.map((conv) => (conv.id === id ? { ...conv, title: nextTitle } : conv))
    )
  }

  const togglePinConversation = (id) => {
    setConversations((prev) =>
      prev.map((conv) => (conv.id === id ? { ...conv, pinned: !conv.pinned } : conv))
    )
  }

  const removeConversation = (id) => {
    setConversations((prev) => {
      const next = prev.filter((conv) => conv.id !== id)
      if (next.length === 0) {
        const fresh = createConversation()
        setActiveConvId(fresh.id)
        return [fresh]
      }
      setActiveConvId((activeId) => (activeId === id ? next[0].id : activeId))
      return next
    })
    setStreamingResponses((prev) => {
      if (!(id in prev)) return prev
      const next = { ...prev }
      delete next[id]
      return next
    })
  }

  const clearStreamingResponse = (convId) => {
    setStreamingResponses((prev) => {
      if (!(convId in prev)) return prev
      const next = { ...prev }
      delete next[convId]
      return next
    })
  }

  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        conversations,
        activeConvId,
      })
    )
  }, [conversations, activeConvId])

  const sendMessage = async (query, options = {}) => {
    let targetConvId = activeConvId
    if (!targetConvId) {
      targetConvId = createNewChat()
    }
    const targetConversation = conversations.find((conv) => conv.id === targetConvId)
    const targetCollection = targetConversation?.collection || targetConvId

    // Add user message
    const userMessage = { role: 'user', content: query }
    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.id !== targetConvId) return conv
        const nextTitle =
          conv.title === NEW_CONV_TITLE
            ? query.slice(0, 40) || NEW_CONV_TITLE
            : conv.title
        return { ...conv, title: nextTitle, messages: [...conv.messages, userMessage] }
      })
    )
    setIsLoading(true)
    setStreamingResponses((prev) => ({ ...prev, [targetConvId]: '' }))

    let fullResponse = ''

    try {
      await chatStream(
        targetCollection,
        query,
        options,
        (token) => {
          fullResponse += token
          setStreamingResponses((prev) => ({ ...prev, [targetConvId]: fullResponse }))
        },
        (sources) => {
          setConversations((prev) =>
            prev.map((conv) => {
              if (conv.id !== targetConvId) return conv
              return {
                ...conv,
                messages: [
                  ...conv.messages,
                  {
                    role: 'assistant',
                    content: fullResponse,
                    sources,
                  },
                ],
              }
            })
          )
          clearStreamingResponse(targetConvId)
        },
        (error) => {
          console.error('Chat error:', error)
          setConversations((prev) =>
            prev.map((conv) =>
              conv.id === targetConvId
                ? {
                    ...conv,
                    messages: [
                      ...conv.messages,
                      { role: 'assistant', content: `Error: ${error}` },
                    ],
                  }
                : conv
            )
          )
          clearStreamingResponse(targetConvId)
        }
      )
    } catch (error) {
      console.error('Chat error:', error)
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === targetConvId
            ? {
                ...conv,
                messages: [
                  ...conv.messages,
                  { role: 'assistant', content: `Error: ${error.message}` },
                ],
              }
            : conv
        )
      )
      clearStreamingResponse(targetConvId)
    } finally {
      setIsLoading(false)
    }
  }

  const uploadFiles = async (files) => {
    let targetConvId = activeConvId
    if (!targetConvId) {
      targetConvId = createNewChat()
    }
    const targetConversation = conversations.find((conv) => conv.id === targetConvId)
    const targetCollection = targetConversation?.collection || targetConvId

    setIsUploading(true)
    try {
      const result = await ingestDocuments(targetCollection, files)
      const uploadCount = Array.isArray(files) ? files.length : 0
      const uploadedNames = Array.isArray(files) ? files.map((file) => file.name) : []
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === targetConvId
            ? {
                ...conv,
                uploadedFiles: Array.from(new Set([...(conv.uploadedFiles || []), ...uploadedNames])),
                hasDocuments: true,
                lastUpload: {
                  count: uploadCount,
                  indexed: result?.indexed ?? 0,
                  at: new Date().toISOString(),
                },
              }
            : conv
        )
      )
      return result
    } catch (error) {
      console.error('Upload error:', error)
      throw error
    } finally {
      setIsUploading(false)
    }
  }

  const clearActiveMessages = () => {
    updateActiveConversation((conv) => ({ ...conv, messages: [] }))
    if (activeConvId) clearStreamingResponse(activeConvId)
  }

  return {
    conversations,
    activeConvId,
    activeConversation,
    messages,
    currentResponse,
    isLoading,
    isUploading,
    createNewChat,
    selectConversation,
    setActiveCollection,
    renameConversation,
    togglePinConversation,
    removeConversation,
    sendMessage,
    uploadFiles,
    clearActiveMessages,
  }
}
