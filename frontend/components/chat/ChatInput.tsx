// components/chat/ChatInput.tsx
'use client'

import { useRef, useState, type KeyboardEvent } from 'react'
import { Send } from 'lucide-react'

interface Props {
  onSend: (question: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  function handleSend() {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    // Reset textarea height
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    // Send on Enter, new line on Shift+Enter
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleInput() {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  return (
    <div className="flex items-end gap-3 bg-white border border-border rounded-2xl px-4 py-3 shadow-sm focus-within:border-primary transition-colors">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        disabled={disabled}
        rows={1}
        placeholder="Ask anything about your notes…"
        className="flex-1 resize-none bg-transparent text-sm text-text placeholder-text-muted focus:outline-none leading-relaxed disabled:opacity-50"
        aria-label="Your question"
      />
      <button
        type="button"
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        aria-label="Send question"
        className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center text-white shrink-0 hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:scale-105 disabled:hover:scale-100"
      >
        <Send size={14} />
      </button>
    </div>
  )
}