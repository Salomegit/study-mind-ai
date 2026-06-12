'use client'

import { useRef, useState } from 'react'
import { UploadCloud, CheckCircle, AlertCircle, FileText, X } from 'lucide-react'
import { useUpload } from '@/hooks/useUpload'

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [subjectName, setSubjectName] = useState('')
  const [documentId, setDocumentId] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const { isUploading, isSuccess, isError, progress, result, error, upload, reset } =
    useUpload()

  // ── Handlers ──────────────────────────────────────────────────────────

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0] ?? null
    setFile(picked)
    // Clear previous result when a new file is picked
    if (picked) reset()
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    const dropped = e.dataTransfer.files[0] ?? null
    setFile(dropped)
    if (dropped) reset()
  }

  function clearFile() {
    setFile(null)
    if (inputRef.current) inputRef.current.value = ''
    reset()
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file || !subjectName.trim()) return

    const ok = await upload(file, subjectName, documentId)
    if (ok) {
      // Clear form on success
      setFile(null)
      setSubjectName('')
      setDocumentId('')
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div className="max-w-3xl mx-auto px-4 py-12 animate-fade-in">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-4xl font-extrabold text-accent">Upload Study Materials</h1>
        <p className="text-text-muted mt-3 text-lg max-w-md mx-auto">
          Add notes, assignments, textbooks, or revision papers and start learning.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-3xl border border-border p-6 md:p-8 space-y-6 shadow-sm">
        {/* Dropzone */}
        <div
          role="button"
          tabIndex={0}
          aria-label="Upload file"
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
          className="bg-white rounded-3xl border-2 border-dashed border-primary/30 hover:border-primary hover:shadow-lg p-10 text-center transition-all cursor-pointer"
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={handleFileChange}
          />

          {file ? (
            <div className="flex items-center justify-center gap-3">
              <FileText size={20} className="text-primary shrink-0" />
              <span className="text-text font-medium truncate max-w-xs">{file.name}</span>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); clearFile() }}
                className="text-text-muted hover:text-error transition-colors"
                aria-label="Remove file"
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <>
              <UploadCloud className="w-12 h-12 text-primary mx-auto mb-3" />
              <p className="text-text font-medium">Click or drag a file here</p>
              <p className="text-text-muted text-sm mt-1">PDF or DOCX · max 20 MB</p>
            </>
          )}
        </div>

        {/* Upload progress bar */}
        {isUploading && (
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs text-text-muted">
              <span>Uploading…</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-border rounded-full h-2 overflow-hidden">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-200"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Subject name */}
        <div>
          <label htmlFor="subject" className="block text-sm font-semibold text-accent mb-1.5">
            Subject Name <span className="text-error">*</span>
          </label>
          <input
            id="subject"
            type="text"
            value={subjectName}
            onChange={(e) => setSubjectName(e.target.value)}
            required
            disabled={isUploading}
            className="w-full bg-background border border-border rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary text-text placeholder-text-muted disabled:opacity-60"
            placeholder="e.g. Biology Form 4, History Revision, Database Systems"
          />
        </div>

        {/* Document ID */}
        <div>
          <label htmlFor="docId" className="block text-sm font-semibold text-accent mb-1.5">
            Document ID{' '}
            <span className="text-text-muted font-normal">(optional)</span>
          </label>
          <input
            id="docId"
            type="text"
            value={documentId}
            onChange={(e) => setDocumentId(e.target.value)}
            disabled={isUploading}
            className="w-full bg-background border border-border rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary text-text placeholder-text-muted disabled:opacity-60"
            placeholder="A unique name for this document"
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isUploading || !file || !subjectName.trim()}
          className="w-full bg-primary text-white rounded-xl font-semibold py-3.5 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 transition-all flex items-center justify-center gap-2 shadow-sm"
        >
          {isUploading ? (
            <>
              <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              Uploading… {progress}%
            </>
          ) : (
            'Upload & Start Learning'
          )}
        </button>
      </form>

      {/* Success */}
      {isSuccess && result && (
        <div className="mt-6 rounded-2xl p-4 flex gap-3 items-start bg-success/10 border border-success/30">
          <CheckCircle className="text-success shrink-0 mt-0.5" size={20} />
          <p className="text-sm text-text">
            Your notes are ready!{' '}
            <span className="font-semibold">{result.chunks_added} sections</span> added
            to <span className="font-semibold">"{result.collection_name}"</span>.
            <a href="/ask" className="ml-2 text-primary underline underline-offset-2">
              Ask a question →
            </a>
          </p>
        </div>
      )}

      {/* Error */}
      {isError && error && (
        <div className="mt-6 rounded-2xl p-4 flex gap-3 items-start bg-error/10 border border-error/30">
          <AlertCircle className="text-error shrink-0 mt-0.5" size={20} />
          <p className="text-sm text-text">{error}</p>
        </div>
      )}
    </div>
  )
}