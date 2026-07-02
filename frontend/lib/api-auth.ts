/**
 * API wrapper with Clerk authentication
 * Automatically includes user ID and role in requests
 */

import { auth } from '@clerk/nextjs/server'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: Record<string, any> | FormData
}

/**
 * Make an authenticated API request to the backend
 * Includes session_id for session-based memory
 */
export async function apiCall(
  endpoint: string,
  options: RequestOptions = {}
): Promise<Response> {
  const { userId } = await auth()

  if (!userId) {
    throw new Error('Unauthorized: Must be signed in')
  }

  const url = `${API_URL}${endpoint}`
  const headers = new Headers(options.headers)

  // Add auth headers
  headers.set('X-User-ID', userId)
  headers.set('X-Clerk-Session', userId) // For backend to track session

  // Set content type if not FormData
  if (!(options.body instanceof FormData) && options.body) {
    headers.set('Content-Type', 'application/json')
  }

  // Prepare body
  let body: BodyInit | null = null
  if (options.body) {
    if (options.body instanceof FormData) {
      body = options.body
    } else {
      body = JSON.stringify(options.body)
    }
  }

  // Create request options without body
  const { body: _, ...restOptions } = options
  const requestOptions: RequestInit = {
    ...restOptions,
    headers,
    ...(body && { body }),
  }

  const response = await fetch(url, requestOptions)

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`API Error: ${response.status} - ${error}`)
  }

  return response
}

/**
 * GET request
 */
export async function apiGet(endpoint: string) {
  const response = await apiCall(endpoint, { method: 'GET' })
  return response.json()
}

/**
 * POST request
 */
export async function apiPost(endpoint: string, body?: Record<string, any>) {
  const response = await apiCall(endpoint, {
    method: 'POST',
    body,
  })
  return response.json()
}

/**
 * PUT request
 */
export async function apiPut(endpoint: string, body?: Record<string, any>) {
  const response = await apiCall(endpoint, {
    method: 'PUT',
    body,
  })
  return response.json()
}

/**
 * DELETE request
 */
export async function apiDelete(endpoint: string) {
  const response = await apiCall(endpoint, { method: 'DELETE' })
  return response.json()
}

/**
 * Upload files with authentication
 */
export async function apiUpload(endpoint: string, formData: FormData) {
  const response = await apiCall(endpoint, {
    method: 'POST',
    body: formData,
  })
  return response.json()
}
