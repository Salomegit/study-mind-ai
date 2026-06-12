// hooks/useUpload.ts
'use client'

import { useCallback, useRef, useState } from 'react'
import {
  uploadDocument,
  UploadApiError,
  UploadValidationError,
  type UploadResponse,
} from '@/lib/api/upload'

// ── State shape ────────────────────────────────────────────────────────────

type UploadStatus = 'idle' | 'uploading' | 'success' | 'error'

interface UploadState {
  status: UploadStatus
  progress: number          // 0–100
  result: UploadResponse | null
  error: string | null
}

const INITIAL_STATE: UploadState = {
  status: 'idle',
  progress: 0,
  result: null,
  error: null,
}

// ── Hook ──────────────────────────────────────────────────────────────────

export function useUpload() {
  const [state, setState] = useState<UploadState>(INITIAL_STATE)
  const abortRef = useRef<AbortController | null>(null)

  const upload = useCallback(
    async (file: File, subjectName: string, documentId?: string) => {
      // Cancel any in-flight request before starting a new one
      abortRef.current?.abort()
      abortRef.current = new AbortController()

      setState({ status: 'uploading', progress: 0, result: null, error: null })

      try {
        const result = await uploadDocument(file, subjectName, documentId, {
          signal: abortRef.current.signal,
          onProgress: ({ percent }) =>
            setState((prev) => ({ ...prev, progress: percent })),
        })

        setState({ status: 'success', progress: 100, result, error: null })
        return result
      } catch (err) {
        // Ignore aborts triggered by the user
        if (err instanceof DOMException && err.name === 'AbortError') {
          setState(INITIAL_STATE)
          return null
        }

        const message =
          err instanceof UploadValidationError || err instanceof UploadApiError
            ? err.message
            : 'Something went wrong. Please try again.'

        setState({ status: 'error', progress: 0, result: null, error: message })
        return null
      }
    },
    [],
  )

  const cancel = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setState(INITIAL_STATE)
  }, [])

  return {
    ...state,
    isIdle: state.status === 'idle',
    isUploading: state.status === 'uploading',
    isSuccess: state.status === 'success',
    isError: state.status === 'error',
    upload,
    cancel,
    reset,
  }
}