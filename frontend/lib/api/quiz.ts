// lib/api/quiz.ts
import { API_BASE_URL } from './config'

// ── Types ──────────────────────────────────────────────────────────────────

export type QuestionType = 'multiple_choice' | 'true_false' | 'short_answer'
export type Difficulty = 'easy' | 'medium' | 'hard'
export type QuizType = 'mixed' | 'multiple_choice_only' | 'true_false_only'

export interface QuizQuestion {
  question_id: number
  question_text: string
  question_type: QuestionType
  options?: string[] // For multiple choice and true/false
  correct_answer?: string | number // Omitted in the response sent to client initially
  explanation?: string
}

export interface QuizGenerationRequest {
  collection: string
  num_questions?: number
  difficulty?: Difficulty
  quiz_type?: QuizType
}

export interface QuizGenerationResponse {
  quiz_id: string
  collection: string
  questions: QuizQuestion[]
  num_questions: number
  difficulty: Difficulty
  quiz_type: QuizType
  error?: string | null
}

export interface AnswerSubmission {
  question_id: number
  user_answer: string | number
}

export interface QuizAnswerRequest {
  quiz_id: string
  answers: AnswerSubmission[]
}

export interface AnswerResult {
  question_id: number
  question_text: string
  user_answer: string | number
  correct_answer: string | number
  is_correct: boolean
  explanation: string
  question_type: QuestionType
}

export interface QuizResultResponse {
  quiz_id: string
  total_questions: number
  correct_count: number
  score_percentage: number
  results: AnswerResult[]
  error?: string | null
}

export class QuizApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
  ) {
    super(message)
    this.name = 'QuizApiError'
  }
}

// ── Service ────────────────────────────────────────────────────────────────

/**
 * Generate a quiz from a document collection.
 */
export async function generateQuiz(
  request: QuizGenerationRequest,
  authToken?: string,
): Promise<QuizGenerationResponse> {
  const url = new URL('/quiz/generate', API_BASE_URL).toString()
  const headers: HeadersInit = { 'Content-Type': 'application/json' }
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`
  }

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.text()
      throw new QuizApiError(
        `Quiz generation failed: ${error}`,
        response.status,
      )
    }

    return await response.json()
  } catch (error) {
    if (error instanceof QuizApiError) throw error
    throw new QuizApiError(
      error instanceof Error ? error.message : 'Unknown error during quiz generation',
      500,
    )
  }
}

/**
 * Check user answers and get results.
 */
export async function checkAnswers(
  request: QuizAnswerRequest,
  authToken?: string,
): Promise<QuizResultResponse> {
  const url = new URL('/quiz/check-answers', API_BASE_URL).toString()
  const headers: HeadersInit = { 'Content-Type': 'application/json' }
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`
  }

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.text()
      throw new QuizApiError(
        `Answer checking failed: ${error}`,
        response.status,
      )
    }

    return await response.json()
  } catch (error) {
    if (error instanceof QuizApiError) throw error
    throw new QuizApiError(
      error instanceof Error ? error.message : 'Unknown error during answer checking',
      500,
    )
  }
}
