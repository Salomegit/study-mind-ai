'use client'
import { motion } from 'framer-motion'
import { BookOpen, Zap, Target, GraduationCap, Users, FlaskConical, Upload, MessageSquare, FileSearch, FolderOpen } from 'lucide-react'

const fadeUp = {
  initial: { opacity: 0, y: 40 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7 },
}

export default function HomePage() {
  return (
    <div>
      {/* ── Hero ── */}
      <section className="relative overflow-hidden py-24 md:py-36">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/8 via-transparent to-secondary/8 pointer-events-none" />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <motion.div {...fadeUp}>
            <h1 className="text-5xl md:text-7xl font-extrabold text-accent leading-tight">
              Study Smarter,<br />
              <span className="text-primary">Not Harder</span>
            </h1>
            <p className="mt-6 text-xl text-text-muted max-w-xl mx-auto">
              Upload your notes, PDFs, and study materials. Ask questions and get simple answers instantly.
            </p>
            <motion.div
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="mt-10 flex flex-wrap justify-center gap-4"
            >
              <a
                href="/upload"
                className="bg-primary hover:bg-primary/90 text-white font-semibold py-3 px-8 rounded-xl transition-all hover:scale-105 shadow-md"
              >
                Upload Notes
              </a>
              <a
                href="/ask"
                className="border border-border hover:border-primary text-text hover:text-primary py-3 px-8 rounded-xl transition-all"
              >
                Ask Questions
              </a>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ── Benefits ── */}
      <section className="py-16 bg-card/20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-accent mb-12">
            Everything you need to learn faster
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <BenefitCard
              emoji="📚"
              title="Learn from your own notes"
              description="Upload class notes, revision papers, or textbooks. StudyMind reads them so you can ask anything."
            />
            <BenefitCard
              emoji="⚡"
              title="Get answers instantly"
              description="No more endless scrolling through PDFs. Ask a question, get a clear answer in seconds."
            />
            <BenefitCard
              emoji="🎯"
              title="Stay focused"
              description="Study only what matters most. Every answer comes directly from your uploaded materials."
            />
          </div>
        </div>
      </section>

      {/* ── Who It's For ── */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-accent mb-12">
            Who is StudyMind for?
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <AudienceCard
              icon={GraduationCap}
              label="KCSE Students"
              description="Revise faster and prepare for exams. Get straight answers from your own revision notes."
            />
            <AudienceCard
              icon={Users}
              label="University Students"
              description="Understand course material more easily. Upload lecture slides and ask anything."
            />
            <AudienceCard
              icon={FlaskConical}
              label="Researchers"
              description="Quickly find information in long documents. Stop searching, start understanding."
            />
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-16 bg-card/20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-accent mb-12">
            Built for how you actually study
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <FeatureCard icon={Upload} title="Upload PDFs & DOCX" description="Drop in any document and start asking questions right away." />
            <FeatureCard icon={MessageSquare} title="Ask Questions Naturally" description="Write questions the way you'd ask a teacher or classmate." />
            <FeatureCard icon={FileSearch} title="View Source References" description="Every answer shows exactly which page it came from." />
            <FeatureCard icon={FolderOpen} title="Organise by Subject" description="Keep Biology, History, and Maths separate in their own collections." />
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className="py-16">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-accent mb-14">How It Works</h2>
          <div className="flex flex-col md:flex-row justify-center items-center gap-6 md:gap-4">
            <Step number="1" title="Upload Notes" description="Add your PDFs, DOCX files, or revision papers." />
            <Arrow />
            <Step number="2" title="Ask Questions" description="Type anything you want to know from your materials." />
            <Arrow />
            <Step number="3" title="Get Answers" description="Receive a clear answer with the source reference." />
          </div>
        </div>
      </section>

      {/* ── Final CTA ── */}
      <section className="py-20 bg-gradient-to-br from-primary/10 to-secondary/10">
        <div className="max-w-2xl mx-auto px-4 text-center">
          <h2 className="text-4xl font-extrabold text-accent mb-4">Ready to study smarter?</h2>
          <p className="text-text-muted text-lg mb-8">Upload your first document today and start getting answers in seconds.</p>
          <a
            href="/upload"
            className="inline-block bg-primary hover:bg-primary/90 text-white font-semibold py-4 px-10 rounded-xl transition-all hover:scale-105 shadow-lg text-lg"
          >
            Get Started
          </a>
        </div>
      </section>
    </div>
  )
}

function BenefitCard({ emoji, title, description }: { emoji: string; title: string; description: string }) {
  return (
    <motion.div
      whileHover={{ y: -8, scale: 1.03 }}
      transition={{ type: 'spring', stiffness: 300 }}
      className="bg-white rounded-3xl p-7 border border-border shadow-sm hover:shadow-md transition-shadow"
    >
      <div className="text-4xl mb-4">{emoji}</div>
      <h3 className="text-xl font-semibold text-accent mb-2">{title}</h3>
      <p className="text-text-muted">{description}</p>
    </motion.div>
  )
}

function AudienceCard({ icon: Icon, label, description }: { icon: any; label: string; description: string }) {
  return (
    <motion.div
      whileHover={{ y: -8, scale: 1.03 }}
      transition={{ type: 'spring', stiffness: 300 }}
      className="bg-white rounded-3xl p-7 border border-border shadow-sm hover:shadow-md transition-shadow text-center"
    >
      <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
        <Icon className="text-primary" size={26} />
      </div>
      <h3 className="text-xl font-semibold text-accent mb-2">{label}</h3>
      <p className="text-text-muted">{description}</p>
    </motion.div>
  )
}

function FeatureCard({ icon: Icon, title, description }: { icon: any; title: string; description: string }) {
  return (
    <motion.div
      whileHover={{ y: -6 }}
      className="bg-white rounded-2xl p-6 border border-border hover:border-primary/40 transition-all hover:shadow-lg"
    >
      <div className="w-11 h-11 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
        <Icon className="text-primary" size={22} />
      </div>
      <h3 className="text-lg font-semibold text-accent mb-1">{title}</h3>
      <p className="text-text-muted text-sm">{description}</p>
    </motion.div>
  )
}

function Step({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <div className="text-center max-w-[200px]">
      <div className="w-18 h-18 w-[72px] h-[72px] rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-2xl font-extrabold text-white mx-auto mb-4 shadow-lg">
        {number}
      </div>
      <h3 className="text-xl font-semibold text-accent">{title}</h3>
      <p className="text-text-muted text-sm mt-1">{description}</p>
    </div>
  )
}

function Arrow() {
  return (
    <div className="text-primary text-3xl font-bold hidden md:block select-none">→</div>
  )
}