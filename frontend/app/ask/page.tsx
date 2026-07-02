'use client'

import { useEffect, useRef, useState } from 'react'
import { Trash2, BookOpen } from 'lucide-react'
import { useAsk } from '@/hooks/useAsk'
import { ChatMessage } from '@/components/chat/ChatMessage'
import { ChatInput } from '@/components/chat/ChatInput'
import { TypingIndicator } from '@/components/chat/TypingIndicator'
import { ProtectedPage } from '@/components/ProtectedRoute'

// ── Empty state ────────────────────────────────────────────────────────────

const SUGGESTIONS = [
  'Summarise the key points from chapter 1',
  'What are the main causes of World War II?',
  'Explain the process of photosynthesis',
  'What formulas should I memorise?',
]

function EmptyState({ onSuggestion }: { onSuggestion: (s: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4 gap-6">
      <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center">
        <BookOpen className="text-primary" size={26} />
      </div>
      <div>
        <h2 className="text-xl font-semibold text-accent">Ask anything about your notes</h2>
        <p className="text-text-muted text-sm mt-1">
          Type a question or pick one below to get started.
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-md">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onSuggestion(s)}
            className="text-left text-sm bg-white border border-border rounded-xl px-4 py-2.5 text-text-muted hover:border-primary hover:text-text transition-colors"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function AskPage() {
  const [subject, setSubject] = useState('')
  const [committed, setCommitted] = useState(false)

  const { messages, isLoading, error, ask, clearChat } = useAsk(subject)

  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  function handleCommit(e: React.FormEvent) {
    e.preventDefault()
    if (subject.trim()) setCommitted(true)
  }

  // ── Subject picker (shown before chat) ──────────────────────────────────

  if (!committed) {
    return (
      <ProtectedPage>
        <div className="max-w-md mx-auto px-4 py-24 animate-fade-in">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-extrabold text-accent">Ask Anything</h1>
          <p className="text-text-muted mt-2">
            Which subject do you want to study?
          </p>
        </div>

        <form onSubmit={handleCommit} className="bg-white rounded-3xl border border-border p-6 shadow-sm space-y-4">
          <div>
            <label htmlFor="subject" className="block text-sm font-semibold text-accent mb-1.5">
              Subject Name
            </label>
            <input
              id="subject"
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
              autoFocus
              className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-text placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g. Biology Form 4, History Revision"
            />
            <p className="text-xs text-text-muted mt-1.5">
              This should match the subject name you used when uploading.
            </p>
          </div>
          <button
            type="submit"
            disabled={!subject.trim()}
            className="w-full bg-primary text-white rounded-xl font-semibold py-3 hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 transition-all"
          >
            Start Studying →
          </button>
        </form>
      </div>
      </ProtectedPage>
    )
  }

  // ── Chat interface ──────────────────────────────────────────────────────

  return (
    <ProtectedPage>
      <div className="max-w-3xl mx-auto px-4 py-6 flex flex-col h-[calc(100vh-80px)] animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div>
          <h1 className="text-xl font-extrabold text-accent">Ask Anything</h1>
          <p className="text-xs text-text-muted">
            Studying:{' '}
            <button
              onClick={() => { clearChat(); setCommitted(false) }}
              className="text-primary underline underline-offset-2 hover:no-underline"
            >
              {subject}
            </button>
          </p>
        </div>

        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="flex items-center gap-1.5 text-xs text-text-muted hover:text-error transition-colors px-3 py-1.5 rounded-lg hover:bg-error/10"
            aria-label="Clear chat"
          >
            <Trash2 size={13} />
            Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-6 pr-1 pb-2">
        {messages.length === 0 ? (
          <EmptyState onSuggestion={(s) => ask(s)} />
        ) : (
          messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
        )}

        {/* Typing indicator */}
        {isLoading && <TypingIndicator />}

        {/* Error inline */}
        {error && (
          <div className="bg-error/10 border border-error/30 rounded-2xl px-4 py-3 text-sm text-error">
            ⚠️ {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="shrink-0 pt-3">
        <ChatInput onSend={ask} disabled={isLoading} />
        <p className="text-center text-[10px] text-text-muted mt-2">
          Enter to send · Shift+Enter for new line
        </p>
      </div>
      </div>
    </ProtectedPage>
  )
}