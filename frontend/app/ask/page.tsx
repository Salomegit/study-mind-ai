'use client'
import { useState } from 'react'
import { askQuestion } from '@/lib/api'
import { Send, Book, Loader2, ExternalLink, TrendingUp } from 'lucide-react'

interface Source {
  chunk_id: string
  text_preview: string
  similarity_score: number
  metadata: { filename?: string; page_number?: number }
}

export default function AskPage() {
  const [collection, setCollection] = useState('')
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState<string | null>(null)
  const [sources, setSources] = useState<Source[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!collection.trim() || !question.trim()) return

    setLoading(true)
    setError(null)
    setAnswer(null)
    setSources([])

    try {
      const data = await askQuestion(collection, question)
      if (data.error) {
        setError(data.error)
      } else {
        setAnswer(data.answer)
        setSources(data.sources || [])
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-12 animate-fade-in">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">Ask Your Document</h1>
        <p className="text-text-muted mt-2">Grounded answers with similarity‑ranked citations</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-surface/50 backdrop-blur-sm rounded-2xl border border-border p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium mb-1">Collection name</label>
          <input type="text" value={collection} onChange={(e) => setCollection(e.target.value)} required className="w-full bg-background border border-border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary" placeholder="e.g., biology-101" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Your question</label>
          <textarea value={question} onChange={(e) => setQuestion(e.target.value)} required rows={3} className="w-full bg-background border border-border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary resize-none" placeholder="What is the process of photosynthesis? Explain the theory of relativity..." />
        </div>
        <button type="submit" disabled={loading || !collection || !question} className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2">
          {loading ? <Loader2 className="animate-spin" /> : <Send size={18} />}
          {loading ? 'Searching chunks & generating answer...' : 'Ask StudyMind'}
        </button>
      </form>

      {error && (
        <div className="mt-6 bg-error/10 border border-error/30 rounded-xl p-4 text-error">
          ⚠️ {error}
        </div>
      )}

      {answer && (
        <div className="mt-8 space-y-6 animate-slide-up">
          <div className="bg-surface rounded-2xl border border-border p-6">
            <div className="flex items-center gap-2 mb-3">
              <Book className="text-primary" size={20} />
              <h2 className="text-xl font-semibold">Answer</h2>
            </div>
            <div className="prose prose-invert max-w-none text-text leading-relaxed whitespace-pre-wrap">
              {answer}
            </div>
          </div>

          {sources.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="text-accent" size={20} />
                <h2 className="text-xl font-semibold">Sources (similarity score)</h2>
              </div>
              <div className="space-y-3">
                {sources.map((src, idx) => (
                  <div key={src.chunk_id} className="bg-surface/30 border border-border rounded-xl p-4 transition hover:border-primary/50">
                    <div className="flex justify-between items-start gap-2 flex-wrap mb-2">
                      <span className="text-xs font-mono bg-primary/20 text-primary px-2 py-0.5 rounded-full">Score: {src.similarity_score}</span>
                      {src.metadata?.filename && <span className="text-xs text-text-muted">📄 {src.metadata.filename}{src.metadata.page_number ? `, p.${src.metadata.page_number}` : ''}</span>}
                    </div>
                    <p className="text-sm text-text-muted">{src.text_preview}</p>
                    <div className="mt-2 text-xs text-primary/70 flex items-center gap-1">
                      <ExternalLink size={12} /> chunk_id: {src.chunk_id}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}