// lib/api/upload.ts

import { API_BASE_URL } from './config'

// ── Types ──────────────────────────────────────────────────────────────────

export interface UploadResponse {
  chunks_added: number
  collection_name: string
  document_id: string
}

export interface UploadProgressEvent {
  percent: number   // 0–100
  loaded: number    // bytes uploaded
  total: number     // bytes total
}

export interface UploadOptions {
  onProgress?: (event: UploadProgressEvent) => void
  signal?: AbortSignal
}

// ── Validation (client-side fast-fail) ────────────────────────────────────

const ALLOWED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]
const MAX_SIZE_MB = 20  // mirror your backend settings.MAX_FILE_SIZE_MB

export class UploadValidationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'UploadValidationError'
  }
}

export class UploadApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
  ) {
    super(message)
    this.name = 'UploadApiError'
  }
}

function validateFile(file: File): void {
  // SECURITY: always re-validate on the server too — this is UX only.
  if (!ALLOWED_TYPES.includes(file.type)) {
    throw new UploadValidationError(
      'Only PDF and DOCX files are supported.',
    )
  }
  const sizeMb = file.size / (1024 * 1024)
  if (sizeMb > MAX_SIZE_MB) {
    throw new UploadValidationError(
      `File is ${sizeMb.toFixed(1)} MB. Maximum allowed is ${MAX_SIZE_MB} MB.`,
    )
  }
}

// ── Core upload function ───────────────────────────────────────────────────

/**
 * Upload a study document to the backend.
 *
 * Uses XMLHttpRequest instead of fetch so we can track upload progress.
 *
 * SECURITY NOTES:
 * - collection_name / document_id go into FormData as plain text.
 *   Your backend should sanitise these (strip path traversal chars, etc.)
 *   before using them as ChromaDB collection names.
 * - file.type can be spoofed by the client — the backend MUST re-validate
 *   the actual file magic bytes / content-type.
 * - If you add auth later, attach the token in the Authorization header
 *   below, never in the URL.
 */
export function uploadDocument(
  file: File,
  subjectName: string,
  documentId?: string,
  options: UploadOptions = {},
): Promise<UploadResponse> {
  // Fast client-side validation before hitting the network
  validateFile(file)

  if (!subjectName.trim()) {
    throw new UploadValidationError('Subject name is required.')
  }

  return new Promise((resolve, reject) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('collection_name', subjectName.trim())
    if (documentId?.trim()) {
      formData.append('document_id', documentId.trim())
    }

    const xhr = new XMLHttpRequest()

    // Progress tracking
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && options.onProgress) {
        options.onProgress({
          percent: Math.round((e.loaded / e.total) * 100),
          loaded: e.loaded,
          total: e.total,
        })
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data: UploadResponse = JSON.parse(xhr.responseText)
          resolve(data)
        } catch {
          reject(new UploadApiError('Unexpected response from server.', xhr.status))
        }
      } else {
        // Parse FastAPI's { detail: string } error shape
        let message = `Upload failed (${xhr.status}).`
        try {
          const err = JSON.parse(xhr.responseText)
          if (err?.detail) message = err.detail
        } catch { /* ignore parse error */ }
        reject(new UploadApiError(message, xhr.status))
      }
    })

    xhr.addEventListener('error', () =>
      reject(new UploadApiError('Network error — check your connection.', 0)),
    )

    xhr.addEventListener('timeout', () =>
      reject(new UploadApiError('Upload timed out. Try a smaller file.', 0)),
    )

    // Abort support
    if (options.signal) {
      options.signal.addEventListener('abort', () => xhr.abort())
    }

    xhr.timeout = 120_000 // 2 min for large files
    xhr.open('POST', `${API_BASE_URL}/upload`)
    // Add auth header here when ready:
    // xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    xhr.send(formData)
  })
}