'use client'
import { useCallback, useRef, useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { askQuestion, AskApiError, type AskResponse, type Source } from '@/lib/api/ask'
import { getSessionHistory } from '@/lib/api/session'

// ── Types ──────────────────────────────────────────────────────────────────

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp: Date
}

type AskStatus = 'idle' | 'loading' | 'error'

interface AskState {
  messages: Message[]
  status: AskStatus
  error: string | null
}

// ── Hook ──────────────────────────────────────────────────────────────────

export function useAsk(collection: string) {
  const [state, setState] = useState<AskState>({
    messages: [],
    status: 'idle',
    error: null,
  })

  const abortRef = useRef<AbortController | null>(null)
  const sessionIdRef = useRef<string>(crypto.randomUUID())
  const { getToken } = useAuth()

  const ask = useCallback(
    async (question: string) => {
      if (!question.trim() || !collection.trim()) return

      // Cancel any in-flight request
      abortRef.current?.abort()
      abortRef.current = new AbortController()

      // Optimistically add the user message immediately
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: question.trim(),
        timestamp: new Date(),
      }

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        status: 'loading',
        error: null,
      }))

      try {
        // Get Clerk auth token
        const token = await getToken()

        const data: AskResponse = await askQuestion({
          collection,
          question: question.trim(),
          sessionId: sessionIdRef.current,
          authToken: token || undefined,
          signal: abortRef.current.signal,
        })

        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
          timestamp: new Date(),
        }

        setState((prev) => ({
          ...prev,
          messages: [...prev.messages, assistantMessage],
          status: 'idle',
          error: null,
        }))

      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          // User navigated away or cancelled — silently revert
          setState((prev) => ({
            ...prev,
            messages: prev.messages.filter((m) => m.id !== userMessage.id),
            status: 'idle',
          }))
          return
        }

        const message =
          err instanceof AskApiError
            ? err.message
            : 'Something went wrong. Please try again.'

        setState((prev) => ({
          ...prev,
          status: 'error',
          error: message,
        }))
      }
    },
    [collection, getToken],
  )

  const clearChat = useCallback(() => {
    abortRef.current?.abort()
    sessionIdRef.current = crypto.randomUUID()
    setState({ messages: [], status: 'idle', error: null })
  }, [])

  // Resume a past chat picked from the "recent chats" list — fetches its
  // saved history and swaps the active session_id so new turns append to it.
  const loadSession = useCallback(async (sessionId: string) => {
    abortRef.current?.abort()
    setState((prev) => ({ ...prev, status: 'loading', error: null }))

    try {
      const token = await getToken()
      const { history } = await getSessionHistory(sessionId, token || undefined)
      sessionIdRef.current = sessionId
      setState({
        messages: history.map((turn) => ({
          id: crypto.randomUUID(),
          role: turn.role,
          content: turn.content,
          timestamp: new Date(),
        })),
        status: 'idle',
        error: null,
      })
    } catch {
      setState((prev) => ({ ...prev, status: 'error', error: 'Could not load that chat.' }))
    }
  }, [getToken])

  return {
    messages: state.messages,
    isLoading: state.status === 'loading',
    error: state.error,
    sessionId: sessionIdRef.current,
    ask,
    clearChat,
    loadSession,
  }
}
