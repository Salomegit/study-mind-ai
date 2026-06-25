'use client'
import { useCallback, useRef, useState } from 'react'
import { askQuestion, AskApiError, type AskResponse, type Source } from '@/lib/api/ask'

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
  const sessionIdRef = useRef<string>(crypto.randomUUID())   // ← new: one UUID per hook instance

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
        const data: AskResponse = await askQuestion({        // ← changed: object call
          collection,
          question: question.trim(),
          sessionId: sessionIdRef.current,                   // ← new: pass session
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
    [collection],
  )

  const clearChat = useCallback(() => {
    abortRef.current?.abort()
    sessionIdRef.current = crypto.randomUUID()               // ← new: fresh session on clear
    setState({ messages: [], status: 'idle', error: null })
  }, [])

  return {
    messages: state.messages,
    isLoading: state.status === 'loading',
    error: state.error,
    ask,
    clearChat,
  }
}
