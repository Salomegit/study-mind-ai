// lib/api/ask.ts
import { API_BASE_URL } from './config'

// ── Types ──────────────────────────────────────────────────────────────────

export interface Source {
  chunk_id: string
  text_preview: string
  similarity_score: number
  metadata: {
    filename?: string
    page_number?: number
  }
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AskResponse {
  answer: string
  sources: Source[]
  num_chunks_retrieved: number
  session_id: string | null        // ← new
  history: ChatMessage[]           // ← new
}

export class AskApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
  ) {
    super(message)
    this.name = 'AskApiError'
  }
}

// ── Service ────────────────────────────────────────────────────────────────

/**
 * Params for askQuestion.
 *
 * SECURITY NOTES:
 * - `collection` goes straight into the request body. Never derive it from
 *   URL params without validation — a user could pass any string and probe
 *   collections they don't own. Add auth + collection ownership checks on
 *   the backend before going to production.
 * - `question` is user-supplied text. Your backend passes it to Gemini;
 *   ensure you're not concatenating it raw into a system prompt in a way
 *   that allows prompt injection (wrap it clearly as user content).
 * - Rate-limit the /ask endpoint on the backend. A single question can
 *   trigger multiple Gemini API calls and ChromaDB reads.
 * - `sessionId` is a client-generated UUID. History is stored server-side
 *   only — the client never sends raw history, so it cannot be tampered with.
 */
export interface AskParams {
  collection: string
  question: string
  sessionId?: string
  signal?: AbortSignal
}

export async function askQuestion({
  collection,
  question,
  sessionId,
  signal,
}: AskParams): Promise<AskResponse> {
  const res = await fetch(`${API_BASE_URL}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ collection, question, session_id: sessionId }),  // ← new
    signal,
  })

  if (!res.ok) {
    let message = `Request failed (${res.status})`
    try {
      const err = await res.json()
      if (err?.detail) message = err.detail
    } catch { /* ignore */ }
    throw new AskApiError(message, res.status)
  }

  return res.json()
}
