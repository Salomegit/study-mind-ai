'use client'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Zap } from 'lucide-react'

interface QuizSetupProps {
  collections: string[]
  onGenerateQuiz: (
    collection: string,
    numQuestions: number,
    difficulty: 'easy' | 'medium' | 'hard',
    quizType: 'mixed' | 'multiple_choice_only' | 'true_false_only',
  ) => Promise<void>
  isLoading: boolean
}

export function QuizSetup({
  collections,
  onGenerateQuiz,
  isLoading,
}: QuizSetupProps) {
  const [selectedCollection, setSelectedCollection] = useState('')
  const [numQuestions, setNumQuestions] = useState(5)
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium')
  const [quizType, setQuizType] = useState<'mixed' | 'multiple_choice_only' | 'true_false_only'>('mixed')

  const handleGenerate = async () => {
    if (!selectedCollection.trim()) {
      alert('Please select a collection')
      return
    }
    await onGenerateQuiz(selectedCollection, numQuestions, difficulty, quizType)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-white rounded-3xl p-8 shadow-sm border border-border max-w-2xl mx-auto"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
          <Zap className="w-5 h-5 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-accent">Generate a Quiz</h2>
      </div>

      <div className="space-y-6">
        {/* Collection selection */}
        <div>
          <label className="block text-sm font-medium text-text mb-2">
            Select Collection
          </label>
          <select
            value={selectedCollection}
            onChange={(e) => setSelectedCollection(e.target.value)}
            className="w-full px-4 py-2 border border-border rounded-lg bg-white text-text focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20"
          >
            <option value="">Choose a collection...</option>
            {collections.map((collection) => (
              <option key={collection} value={collection}>
                {collection}
              </option>
            ))}
          </select>
        </div>

        {/* Number of questions */}
        <div>
          <label className="block text-sm font-medium text-text mb-2">
            Number of Questions: <span className="text-primary font-semibold">{numQuestions}</span>
          </label>
          <input
            type="range"
            min="1"
            max="20"
            value={numQuestions}
            onChange={(e) => setNumQuestions(parseInt(e.target.value))}
            className="w-full h-2 bg-border rounded-lg appearance-none cursor-pointer accent-primary"
          />
          <div className="flex justify-between text-xs text-text-muted mt-1">
            <span>1</span>
            <span>20</span>
          </div>
        </div>

        {/* Difficulty level */}
        <div>
          <label className="block text-sm font-medium text-text mb-3">
            Difficulty Level
          </label>
          <div className="grid grid-cols-3 gap-3">
            {(['easy', 'medium', 'hard'] as const).map((level) => (
              <button
                key={level}
                onClick={() => setDifficulty(level)}
                className={`px-4 py-2 rounded-xl font-medium transition-all capitalize ${
                  difficulty === level
                    ? 'bg-primary text-white shadow-sm'
                    : 'bg-card/30 border border-border text-text hover:border-primary/40 hover:bg-primary/5'
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        </div>

        {/* Quiz type */}
        <div>
          <label className="block text-sm font-medium text-text mb-3">
            Question Types
          </label>
          <div className="space-y-2">
            {([
              { value: 'mixed', label: 'Mixed (Multiple Choice, True/False, Short Answer)' },
              { value: 'multiple_choice_only', label: 'Multiple Choice Only' },
              { value: 'true_false_only', label: 'True/False Only' },
            ] as const).map((option) => (
              <label
                key={option.value}
                className={`flex items-center p-3 border rounded-xl cursor-pointer transition-all ${
                  quizType === option.value
                    ? 'border-primary bg-primary/8'
                    : 'border-border hover:border-primary/40 hover:bg-primary/5'
                }`}
              >
                <input
                  type="radio"
                  name="quiz-type"
                  value={option.value}
                  checked={quizType === option.value}
                  onChange={(e) => setQuizType(e.target.value as typeof quizType)}
                  className="w-4 h-4 accent-primary"
                />
                <span className="ml-3 text-text">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Generate button */}
        <button
          onClick={handleGenerate}
          disabled={isLoading || !selectedCollection}
          className={`w-full py-3 px-4 rounded-xl font-semibold transition-all ${
            isLoading || !selectedCollection
              ? 'bg-border text-text-muted cursor-not-allowed'
              : 'bg-primary hover:bg-primary/90 text-white hover:scale-105 shadow-md'
          }`}
        >
          {isLoading ? 'Generating Quiz...' : 'Generate Quiz'}
        </button>
      </div>
    </motion.div>
  )
}
