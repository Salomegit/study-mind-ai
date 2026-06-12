export default function Footer() {
  return (
    <footer className="border-t border-border py-6 mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-text-muted text-sm">
        <p>StudyMind AI – RAG-powered study assistant for KCSE, university & researchers.</p>
        <p className="mt-1">© {new Date().getFullYear()} – Answers grounded in your documents</p>
      </div>
    </footer>
  )
}