// lib/api/session.ts
import { API_BASE_URL } from './config'
import type { ChatMessage } from './ask'

// ── Types ──────────────────────────────────────────────────────────────────

export interface RecentSession {
  session_id: string
  collection: string | null
  preview: string
  turns: number
  updated_at: string
}

export interface SessionHistory {
  session_id: string
  history: ChatMessage[]
  turns: number
}

// ── Service ────────────────────────────────────────────────────────────────
//
// These endpoints require a Clerk auth token — the backend scopes recent
// chats to the caller's user_id (see backend/routers/session.py). Without
// authToken, all three requests will 401.

function authHeaders(authToken?: string): HeadersInit {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {}
}

export async function listSessions(authToken?: string, signal?: AbortSignal): Promise<RecentSession[]> {
  const res = await fetch(`${API_BASE_URL}/sessions`, { headers: authHeaders(authToken), signal })
  if (!res.ok) throw new Error(`Failed to load recent chats (${res.status})`)
  const data = await res.json()
  return data.sessions
}

export async function getSessionHistory(sessionId: string, authToken?: string): Promise<SessionHistory> {
  const res = await fetch(`${API_BASE_URL}/session/${sessionId}/history`, { headers: authHeaders(authToken) })
  if (!res.ok) throw new Error(`Failed to load chat history (${res.status})`)
  return res.json()
}

export async function deleteSession(sessionId: string, authToken?: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/session/${sessionId}`, {
    method: 'DELETE',
    headers: authHeaders(authToken),
  })
  if (!res.ok) throw new Error(`Failed to delete chat (${res.status})`)
}
