// components/chat/RecentChats.tsx
'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { MessageSquare, Trash2 } from 'lucide-react'
import { listSessions, deleteSession, type RecentSession } from '@/lib/api/session'

interface Props {
  activeSessionId?: string
  onSelect: (session: RecentSession) => void
  /** Bumped by the parent whenever a new turn is saved, to refresh the list. */
  refreshKey?: number
}

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso + 'Z').getTime()
  const minutes = Math.floor(diffMs / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export function RecentChats({ activeSessionId, onSelect, refreshKey }: Props) {
  const [sessions, setSessions] = useState<RecentSession[]>([])
  const [loading, setLoading] = useState(true)
  const { getToken } = useAuth()

  useEffect(() => {
    const controller = new AbortController()
    getToken()
      .then((token) => listSessions(token || undefined, controller.signal))
      .then(setSessions)
      .catch(() => { /* non-critical — leave list empty */ })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [refreshKey, getToken])

  async function handleDelete(e: React.MouseEvent, sessionId: string) {
    e.stopPropagation()
    setSessions((prev) => prev.filter((s) => s.session_id !== sessionId))
    try {
      const token = await getToken()
      await deleteSession(sessionId, token || undefined)
    } catch {
      // already removed from UI; a stale row on the server will just TTL-expire
    }
  }

  if (loading) {
    return <p className="text-xs text-text-muted px-2">Loading recent chats...</p>
  }

  if (sessions.length === 0) {
    return <p className="text-xs text-text-muted px-2">No recent chats yet.</p>
  }

  return (
    <div className="space-y-1">
      <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide px-2 mb-2">
        Recent Chats
      </h3>
      {sessions.map((s) => (
        <button
          key={s.session_id}
          onClick={() => onSelect(s)}
          className={`w-full text-left px-3 py-2.5 rounded-xl flex items-start gap-2 group transition-colors
            ${s.session_id === activeSessionId
              ? 'bg-primary/10 border border-primary/30'
              : 'hover:bg-background border border-transparent'
            }`}
        >
          <MessageSquare size={14} className="text-text-muted mt-0.5 shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold text-accent truncate">
              {s.collection || 'Untitled chat'}
            </p>
            <p className="text-xs text-text-muted truncate">{s.preview || `${s.turns} messages`}</p>
            <p className="text-[10px] text-text-muted mt-0.5">{timeAgo(s.updated_at)}</p>
          </div>
          <span
            role="button"
            onClick={(e) => handleDelete(e, s.session_id)}
            className="opacity-0 group-hover:opacity-100 text-text-muted hover:text-error transition-opacity shrink-0 p-1"
            aria-label="Delete chat"
          >
            <Trash2 size={12} />
          </span>
        </button>
      ))}
    </div>
  )
}
