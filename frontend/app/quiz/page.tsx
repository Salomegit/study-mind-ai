'use client'
import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronLeft, AlertCircle, Loader } from 'lucide-react'
import Link from 'next/link'

import { useQuiz } from '@/hooks/useQuiz'
import { QuizSetup } from '@/components/quiz/QuizSetup'
import { QuestionCard } from '@/components/quiz/QuestionCard'
import { QuizResults } from '@/components/quiz/QuizResults'
import { ProtectedPage } from '@/components/ProtectedRoute'
import { API_BASE_URL } from '@/lib/api/config'

export default function QuizPage() {
  const [collections, setCollections] = useState<string[]>([])
  const [collectionsLoaded, setCollectionsLoaded] = useState(false)
  const quiz = useQuiz()

  useEffect(() => {
    const loadCollections = async () => {
      try {
        const url = new URL('/collections', API_BASE_URL).toString()
        const response = await fetch(url)
        if (response.ok) {
          const data = await response.json()
          setCollections(data.collections || [])
        }
      } catch (error) {
        console.error('Failed to load collections:', error)
      } finally {
        setCollectionsLoaded(true)
      }
    }

    loadCollections()
  }, [])

  const handleGenerateQuiz = async (
    collection: string,
    numQuestions: number,
    difficulty: 'easy' | 'medium' | 'hard',
    quizType: 'mixed' | 'multiple_choice_only' | 'true_false_only',
  ) => {
    await quiz.generateNewQuiz(collection, numQuestions, difficulty, quizType)
  }

  return (
    <ProtectedPage>
      <div className="min-h-screen bg-gradient-to-br from-background to-background/90">
      {/* Header */}
      <header className="border-b border-border bg-white/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Link
              href="/"
              className="flex items-center gap-2 text-text-muted hover:text-text transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
              Back
            </Link>
            <h1 className="text-2xl font-bold text-accent">Quiz Generator</h1>
            <div className="w-10" />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <AnimatePresence mode="wait">
          {/* Error state */}
          {quiz.error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3"
            >
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-red-900">Error</p>
                <p className="text-sm text-red-800">{quiz.error}</p>
              </div>
            </motion.div>
          )}

          {/* Loading state */}
          {quiz.status === 'generating' && (
            <motion.div
              key="generating"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-24"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              >
                <Loader className="w-12 h-12 text-primary" />
              </motion.div>
              <p className="mt-4 text-lg text-text-muted">Generating your quiz...</p>
              <p className="text-sm text-text-muted mt-2">
                This may take a moment as we create questions based on your materials.
              </p>
            </motion.div>
          )}

          {/* Checking answers state */}
          {quiz.status === 'checking' && (
            <motion.div
              key="checking"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-24"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              >
                <Loader className="w-12 h-12 text-primary" />
              </motion.div>
              <p className="mt-4 text-lg text-text-muted">Checking your answers...</p>
            </motion.div>
          )}

          {/* Setup state */}
          {quiz.status === 'idle' && (
            <motion.div
              key="setup"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
            >
              {collectionsLoaded ? (
                <>
                  {collections.length === 0 ? (
                    <motion.div className="text-center py-12">
                      <AlertCircle className="w-12 h-12 text-yellow-600 mx-auto mb-4" />
                      <h2 className="text-xl font-bold text-accent mb-2">No Collections Found</h2>
                      <p className="text-text-muted mb-6">
                        You need to upload documents first to create a quiz.
                      </p>
                      <Link
                        href="/upload"
                        className="inline-block bg-primary hover:bg-primary/90 text-white font-semibold py-2 px-6 rounded-lg transition-all"
                      >
                        Upload Documents
                      </Link>
                    </motion.div>
                  ) : (
                    <QuizSetup
                      collections={collections}
                      onGenerateQuiz={handleGenerateQuiz}
                      isLoading={false}
                    />
                  )}
                </>
              ) : (
                <div className="flex justify-center py-12">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                  >
                    <Loader className="w-8 h-8 text-primary" />
                  </motion.div>
                </div>
              )}
            </motion.div>
          )}

          {/* Quiz taking state */}
          {quiz.status === 'quiz_ready' && quiz.currentQuestion && (
            <motion.div
              key="quiz"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="space-y-6"
            >
              <QuestionCard
                question={quiz.currentQuestion}
                answer={quiz.userAnswers[quiz.currentQuestion.question_id]}
                onAnswerChange={quiz.answerQuestion}
                currentIndex={quiz.currentQuestionIndex}
                totalQuestions={quiz.quiz?.questions.length || 0}
                onPrevious={quiz.previousQuestion}
                onNext={quiz.nextQuestion}
              />

              {/* Submit button (only on last question) */}
              {quiz.currentQuestionIndex === (quiz.quiz?.questions.length || 0) - 1 && (
                <motion.button
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  onClick={quiz.submitQuiz}
                  className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-3 px-4 rounded-lg transition-all hover:scale-105"
                >
                  Submit Quiz
                </motion.button>
              )}

              {/* Answer summary */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="bg-primary/8 border border-primary/20 rounded-lg p-4"
              >
                <p className="text-sm text-text-muted">
                  <span className="font-semibold text-text">
                    {Object.keys(quiz.userAnswers).length}
                  </span>
                  {' of '}
                  <span className="font-semibold text-text">
                    {quiz.quiz?.questions.length}
                  </span>
                  {' questions answered'}
                </p>
              </motion.div>
            </motion.div>
          )}

          {/* Results state */}
          {quiz.status === 'results' && quiz.results && (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
            >
              <QuizResults
                results={quiz.results}
                onRetake={quiz.resetQuiz}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
      </div>
    </ProtectedPage>
  )
}
