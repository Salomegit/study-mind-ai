'use client'
import { motion } from 'framer-motion'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { QuizQuestion } from '@/lib/api/quiz'

interface QuestionCardProps {
  question: QuizQuestion
  answer: string | number | undefined
  onAnswerChange: (questionId: number, answer: string | number) => void
  currentIndex: number
  totalQuestions: number
  onPrevious: () => void
  onNext: () => void
}

export function QuestionCard({
  question,
  answer,
  onAnswerChange,
  currentIndex,
  totalQuestions,
  onPrevious,
  onNext,
}: QuestionCardProps) {
  const isMultipleChoice = question.question_type === 'multiple_choice'
  const isTrueFalse = question.question_type === 'true_false'
  const isShortAnswer = question.question_type === 'short_answer'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className="bg-white rounded-xl p-8 shadow-lg border border-border"
    >
      {/* Progress bar */}
      <div className="flex items-center justify-between mb-6">
        <span className="text-sm font-medium text-text-muted">
          Question {currentIndex + 1} of {totalQuestions}
        </span>
        <div className="flex-1 ml-4 h-2 bg-border rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / totalQuestions) * 100}%` }}
          />
        </div>
      </div>

      {/* Question text */}
      <h3 className="text-xl font-semibold text-accent mb-6">
        {question.question_text}
      </h3>

      {/* Answer options */}
      <div className="space-y-3 mb-8">
        {isMultipleChoice && question.options && (
          <div className="space-y-3">
            {question.options.map((option, idx) => (
              <label
                key={idx}
                className={`flex items-center p-4 border rounded-lg cursor-pointer transition-all ${
                  answer === option
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <input
                  type="radio"
                  name={`question-${question.question_id}`}
                  value={option}
                  checked={answer === option}
                  onChange={(e) =>
                    onAnswerChange(question.question_id, e.target.value)
                  }
                  className="w-4 h-4 accent-primary"
                />
                <span className="ml-3 text-text">{option}</span>
              </label>
            ))}
          </div>
        )}

        {isTrueFalse && question.options && (
          <div className="grid grid-cols-2 gap-4">
            {question.options.map((option, idx) => (
              <button
                key={idx}
                onClick={() => onAnswerChange(question.question_id, option)}
                className={`p-4 border rounded-lg font-medium transition-all ${
                  answer === option
                    ? 'border-primary bg-primary text-white'
                    : 'border-border text-text hover:border-primary/50 hover:bg-primary/5'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        )}

        {isShortAnswer && (
          <textarea
            value={answer || ''}
            onChange={(e) =>
              onAnswerChange(question.question_id, e.target.value)
            }
            placeholder="Type your answer here..."
            className="w-full p-4 border border-border rounded-lg bg-white text-text placeholder:text-text-muted focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 resize-none"
            rows={4}
          />
        )}
      </div>

      {/* Navigation buttons */}
      <div className="flex justify-between items-center">
        <button
          onClick={onPrevious}
          disabled={currentIndex === 0}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
            currentIndex === 0
              ? 'opacity-50 cursor-not-allowed text-text-muted'
              : 'text-primary hover:bg-primary/10'
          }`}
        >
          <ChevronLeft className="w-4 h-4" />
          Previous
        </button>

        <div className="text-sm text-text-muted">
          {answer !== undefined ? '✓ Answered' : 'Not answered'}
        </div>

        <button
          onClick={onNext}
          disabled={currentIndex === totalQuestions - 1}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
            currentIndex === totalQuestions - 1
              ? 'opacity-50 cursor-not-allowed text-text-muted'
              : 'text-primary hover:bg-primary/10'
          }`}
        >
          Next
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  )
}
