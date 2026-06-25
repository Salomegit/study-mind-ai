'use client'
import { useCallback, useState } from 'react'
import {
  generateQuiz,
  checkAnswers,
  QuizApiError,
  type QuizGenerationRequest,
  type QuizGenerationResponse,
  type QuizAnswerRequest,
  type QuizResultResponse,
  type QuizQuestion,
  type AnswerSubmission,
} from '@/lib/api/quiz'

// ── Types ──────────────────────────────────────────────────────────────────

type QuizStatus = 'idle' | 'generating' | 'quiz_ready' | 'checking' | 'results' | 'error'

interface QuizState {
  status: QuizStatus
  quiz: QuizGenerationResponse | null
  results: QuizResultResponse | null
  error: string | null
  currentQuestionIndex: number
  userAnswers: Record<number, string | number> // question_id -> answer
}

// ── Hook ──────────────────────────────────────────────────────────────────

export function useQuiz(initialCollection: string = '') {
  const [state, setState] = useState<QuizState>({
    status: 'idle',
    quiz: null,
    results: null,
    error: null,
    currentQuestionIndex: 0,
    userAnswers: {},
  })

  // Generate a new quiz
  const generateNewQuiz = useCallback(
    async (
      collection: string,
      numQuestions: number = 5,
      difficulty: 'easy' | 'medium' | 'hard' = 'medium',
      quizType: 'mixed' | 'multiple_choice_only' | 'true_false_only' = 'mixed',
    ) => {
      if (!collection.trim()) {
        setState((prev) => ({
          ...prev,
          status: 'error',
          error: 'Please select a collection',
        }))
        return
      }

      setState((prev) => ({
        ...prev,
        status: 'generating',
        error: null,
      }))

      try {
        const request: QuizGenerationRequest = {
          collection: collection.trim(),
          num_questions: numQuestions,
          difficulty,
          quiz_type: quizType,
        }

        const response = await generateQuiz(request)

        if (response.error) {
          setState((prev) => ({
            ...prev,
            status: 'error',
            error: response.error,
          }))
          return
        }

        setState((prev) => ({
          ...prev,
          status: 'quiz_ready',
          quiz: response,
          currentQuestionIndex: 0,
          userAnswers: {},
          error: null,
        }))
      } catch (error) {
        const message =
          error instanceof QuizApiError
            ? error.message
            : 'Failed to generate quiz. Please try again.'

        setState((prev) => ({
          ...prev,
          status: 'error',
          error: message,
        }))
      }
    },
    [],
  )

  // Move to next question
  const nextQuestion = useCallback(() => {
    setState((prev) => {
      if (!prev.quiz) return prev
      if (prev.currentQuestionIndex < prev.quiz.questions.length - 1) {
        return {
          ...prev,
          currentQuestionIndex: prev.currentQuestionIndex + 1,
        }
      }
      return prev
    })
  }, [])

  // Move to previous question
  const previousQuestion = useCallback(() => {
    setState((prev) => {
      if (prev.currentQuestionIndex > 0) {
        return {
          ...prev,
          currentQuestionIndex: prev.currentQuestionIndex - 1,
        }
      }
      return prev
    })
  }, [])

  // Record an answer
  const answerQuestion = useCallback((questionId: number, answer: string | number) => {
    setState((prev) => ({
      ...prev,
      userAnswers: {
        ...prev.userAnswers,
        [questionId]: answer,
      },
    }))
  }, [])

  // Submit answers and check them
  const submitQuiz = useCallback(async () => {
    if (!state.quiz) {
      setState((prev) => ({
        ...prev,
        status: 'error',
        error: 'No quiz loaded',
      }))
      return
    }

    // Check if all questions are answered
    if (Object.keys(state.userAnswers).length !== state.quiz.questions.length) {
      setState((prev) => ({
        ...prev,
        status: 'error',
        error: 'Please answer all questions before submitting',
      }))
      return
    }

    setState((prev) => ({
      ...prev,
      status: 'checking',
    }))

    try {
      // Convert answers to submission format
      const answers: AnswerSubmission[] = state.quiz.questions.map((q) => ({
        question_id: q.question_id,
        user_answer: state.userAnswers[q.question_id],
      }))

      const request: QuizAnswerRequest = {
        quiz_id: state.quiz.quiz_id,
        answers,
      }

      const response = await checkAnswers(request)

      if (response.error) {
        setState((prev) => ({
          ...prev,
          status: 'error',
          error: response.error,
        }))
        return
      }

      setState((prev) => ({
        ...prev,
        status: 'results',
        results: response,
        error: null,
      }))
    } catch (error) {
      const message =
        error instanceof QuizApiError
          ? error.message
          : 'Failed to check answers. Please try again.'

      setState((prev) => ({
        ...prev,
        status: 'error',
        error: message,
      }))
    }
  }, [state.quiz, state.userAnswers])

  // Reset quiz
  const resetQuiz = useCallback(() => {
    setState({
      status: 'idle',
      quiz: null,
      results: null,
      error: null,
      currentQuestionIndex: 0,
      userAnswers: {},
    })
  }, [])

  // Get current question
  const currentQuestion: QuizQuestion | null =
    state.quiz && state.currentQuestionIndex < state.quiz.questions.length
      ? state.quiz.questions[state.currentQuestionIndex]
      : null

  return {
    // State
    status: state.status,
    quiz: state.quiz,
    results: state.results,
    error: state.error,
    currentQuestion,
    currentQuestionIndex: state.currentQuestionIndex,
    userAnswers: state.userAnswers,

    // Actions
    generateNewQuiz,
    nextQuestion,
    previousQuestion,
    answerQuestion,
    submitQuiz,
    resetQuiz,
  }
}
