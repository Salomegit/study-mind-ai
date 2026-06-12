'use client'
import { useState } from 'react'
import { uploadDocument } from '@/lib/api'
import { UploadCloud, CheckCircle, AlertCircle, FileText } from 'lucide-react'

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [collectionName, setCollectionName] = useState('')
  const [documentId, setDocumentId] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ success?: boolean; message?: string; error?: string; chunks_added?: number } | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || !collectionName.trim()) return

    setLoading(true)
    setResult(null)
    try {
      const data = await uploadDocument(file, collectionName, documentId.trim() || undefined)
      setResult({ success: true, message: `✅ Success! ${data.chunks_added} chunks added to "${collectionName}".`, chunks_added: data.chunks_added })
      setFile(null)
      setCollectionName('')
      setDocumentId('')
    } catch (err: any) {
      setResult({ success: false, error: err.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-12 animate-fade-in">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">Upload Document</h1>
        <p className="text-text-muted mt-2">PDF or DOCX – your data stays local in ChromaDB</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-surface/50 backdrop-blur-sm rounded-2xl border border-border p-6 md:p-8 space-y-6">
        {/* File dropzone */}
        <div className="border-2 border-dashed border-border rounded-xl p-6 text-center hover:border-primary transition-colors cursor-pointer" onClick={() => document.getElementById('file-input')?.click()}>
          <input id="file-input" type="file" accept=".pdf,.docx" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          <UploadCloud className="w-12 h-12 text-primary mx-auto mb-3" />
          {file ? (
            <div className="flex items-center justify-center gap-2 text-primary">
              <FileText size={18} /> <span>{file.name}</span>
            </div>
          ) : (
            <p className="text-text-muted">Click or drag to upload PDF/DOCX</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Collection name *</label>
          <input type="text" value={collectionName} onChange={(e) => setCollectionName(e.target.value)} required className="w-full bg-background border border-border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary" placeholder="e.g., biology-101, kcse-history" />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Document ID (optional)</label>
          <input type="text" value={documentId} onChange={(e) => setDocumentId(e.target.value)} className="w-full bg-background border border-border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary" placeholder="unique identifier for this document" />
        </div>

        <button type="submit" disabled={loading || !file || !collectionName} className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2">
          {loading ? 'Processing...' : 'Upload & Index'}
        </button>
      </form>

      {result && (
        <div className={`mt-6 rounded-xl p-4 flex gap-3 items-start ${result.success ? 'bg-success/10 border border-success/30' : 'bg-error/10 border border-error/30'}`}>
          {result.success ? <CheckCircle className="text-success shrink-0" /> : <AlertCircle className="text-error shrink-0" />}
          <div className="text-sm">{result.success ? result.message : result.error}</div>
        </div>
      )}
    </div>
  )
}