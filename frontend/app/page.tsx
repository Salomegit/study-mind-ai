import { Sparkles, FileText, Zap, Shield, BookOpen, GraduationCap, BarChart } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="animate-fade-in">
      {/* Hero section */}
      <section className="relative overflow-hidden py-20 md:py-32">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-secondary/5 pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-flex items-center gap-2 bg-primary/10 backdrop-blur-sm rounded-full px-4 py-1.5 mb-6 border border-primary/30">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary">RAG-Powered • No Hallucinations</span>
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold bg-gradient-to-r from-primary via-accent to-secondary bg-clip-text text-transparent">
            Study Smarter with AI
          </h1>
          <p className="mt-6 text-xl text-text-muted max-w-2xl mx-auto">
            Upload your PDFs, lecture notes, or research papers. Ask anything – get precise answers with citations from your own documents.
          </p>
          <div className="mt-10 flex flex-wrap justify-center gap-4">
            <a href="/upload" className="bg-primary hover:bg-primary/90 text-white font-semibold py-3 px-8 rounded-xl transition-all transform hover:scale-105 shadow-lg">
              Upload Document →
            </a>
            <a href="/ask" className="border border-border hover:border-primary text-text hover:text-primary py-3 px-8 rounded-xl transition-all">
              Start Asking
            </a>
          </div>
        </div>
      </section>

      {/* Features grid */}
      <section className="py-16 bg-surface/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">
            Why <span className="text-primary">StudyMind</span>?
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard icon={FileText} title="Ground Truth RAG" description="Answers are extracted directly from your uploaded documents – no generic internet guesses. Our retrieval system scores relevance before answering." />
            <FeatureCard icon={Zap} title="Blazing Fast" description="Powered by Gemini 2.5 Flash & ChromaDB with cosine similarity. Get answers in seconds, even with hundreds of pages." />
            <FeatureCard icon={Shield} title="Privacy First" description="Your documents stay in your local ChromaDB. No third‑party storage – you control everything." />
            <FeatureCard icon={BookOpen} title="KCSE Optimized" description="Simplified language for Kenyan high school students, yet deep enough for university research." />
            <FeatureCard icon={GraduationCap} title="Study Any Subject" description="Mathematics, History, Biology, Literature – any PDF or DOCX works. Create multiple collections to organize courses." />
            <FeatureCard icon={BarChart} title="Smart Citations" description="Every answer includes source chunks with similarity scores and page references. Verify the AI's work instantly." />
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-8">How It Works</h2>
          <div className="flex flex-col md:flex-row justify-center items-center gap-8">
            <Step number="1" title="Upload" description="PDF or DOCX – give your collection a name" />
            <div className="text-primary text-3xl font-bold hidden md:block">→</div>
            <Step number="2" title="Ask" description="Type any question about your document" />
            <div className="text-primary text-3xl font-bold hidden md:block">→</div>
            <Step number="3" title="Get Answers" description="AI cites exact chunks with relevance scores" />
          </div>
        </div>
      </section>
    </div>
  )
}

function FeatureCard({ icon: Icon, title, description }: { icon: any; title: string; description: string }) {
  return (
    <div className="bg-surface/50 backdrop-blur-sm rounded-2xl p-6 border border-border hover:border-primary/50 transition-all hover:shadow-xl group">
      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
        <Icon className="text-primary" size={24} />
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-text-muted">{description}</p>
    </div>
  )
}

function Step({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <div className="text-center max-w-[200px]">
      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-2xl font-bold mx-auto mb-4 shadow-lg">
        {number}
      </div>
      <h3 className="text-xl font-semibold">{title}</h3>
      <p className="text-text-muted text-sm mt-1">{description}</p>
    </div>
  )
}