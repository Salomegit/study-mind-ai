// lib/api/config.ts

/**
 * Central API configuration.
 *
 * SECURITY NOTE: Never expose secrets here. This file is bundled into
 * the client. API keys belong in backend/.env only.
 *
 * Set NEXT_PUBLIC_API_URL in your .env.local:
 *   NEXT_PUBLIC_API_URL=http://localhost:8000
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

/** Reusable base fetch with timeout and standard headers. */
export async function apiFetch(
  path: string,
  init: RequestInit = {},
  timeoutMs = 30_000,
): Promise<Response> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
      // SECURITY: tighten CORS — only send credentials if your backend
      // explicitly sets Access-Control-Allow-Credentials: true
      // credentials: 'include',
    })
    return res
  } finally {
    clearTimeout(timer)
  }
}