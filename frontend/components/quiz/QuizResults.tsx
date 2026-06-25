'use client'
import { motion } from 'framer-motion'
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import { QuizResultResponse } from '@/lib/api/quiz'

interface QuizResultsProps {
  results: QuizResultResponse
  onRetake: () => void
}

export function QuizResults({ results, onRetake }: QuizResultsProps) {
  const scoreColor =
    results.score_percentage >= 80
      ? 'text-green-600'
      : results.score_percentage >= 60
        ? 'text-yellow-600'
        : 'text-red-600'

  const scoreBgColor =
    results.score_percentage >= 80
      ? 'bg-green-50 border-green-200'
      : results.score_percentage >= 60
        ? 'bg-yellow-50 border-yellow-200'
        : 'bg-red-50 border-red-200'

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="space-y-8"
    >
      {/* Score summary */}
      <div className={`rounded-xl p-8 border ${scoreBgColor}`}>
        <div className="text-center">
          <h2 className="text-3xl font-bold text-accent mb-2">Quiz Complete!</h2>
          <div className={`text-5xl font-extrabold ${scoreColor} mb-4`}>
            {results.score_percentage.toFixed(0)}%
          </div>
          <p className="text-lg text-text-muted mb-4">
            You got <span className="font-bold text-text">{results.correct_count}</span> out of{' '}
            <span className="font-bold text-text">{results.total_questions}</span> questions correct
          </p>
          <button
            onClick={onRetake}
            className="mt-6 bg-primary hover:bg-primary/90 text-white font-semibold py-2 px-6 rounded-lg transition-all hover:scale-105"
          >
            Take Another Quiz
          </button>
        </div>
      </div>

      {/* Detailed results */}
      <div className="space-y-4">
        <h3 className="text-2xl font-bold text-accent">Question Breakdown</h3>

        {results.results.map((result, idx) => (
          <motion.div
            key={result.question_id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="bg-white rounded-2xl p-6 shadow-sm border border-border"
          >
            {/* Question header */}
            <div className="flex items-start gap-3 mb-3">
              {result.is_correct ? (
                <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
              ) : (
                <XCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-1" />
              )}
              <div className="flex-1">
                <p className="font-semibold text-text mb-2">
                  {idx + 1}. {result.question_text}
                </p>
                <p className="text-sm text-text-muted mb-3">
                  Type: <span className="capitalize">{result.question_type.replace('_', ' ')}</span>
                </p>
              </div>
            </div>

            {/* Answer info */}
            <div className="ml-9 space-y-2 mb-4 bg-card/30 border border-border p-4 rounded-xl">
              <div>
                <p className="text-sm font-medium text-text-muted">Your answer:</p>
                <p className="text-text">
                  {result.user_answer || <em className="text-text-muted">No answer provided</em>}
                </p>
              </div>

              {!result.is_correct && (
                <div>
                  <p className="text-sm font-medium text-text-muted">Correct answer:</p>
                  <p className="text-text font-semibold">{result.correct_answer}</p>
                </div>
              )}
            </div>

            {/* Explanation */}
            {result.explanation && (
              <div className="ml-9 bg-primary/8 border border-primary/20 rounded-xl p-4">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-accent mb-1">Explanation:</p>
                    <p className="text-sm text-text-muted">{result.explanation}</p>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}
