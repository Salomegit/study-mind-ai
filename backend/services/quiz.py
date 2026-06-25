"""
Quiz generation service — LLM-based quiz question generation.

This service:
1. Retrieves relevant context from ChromaDB
2. Constructs a prompt asking Gemini to generate quiz questions
3. Parses the structured JSON response
4. Validates questions and answers
"""

import json
import logging
import uuid
import google.generativeai as genai

from config import settings
from .retriever import Retriever
from .collection_manager import CollectionManager
from .prompts import _BASE_SYSTEM
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class QuizGenerator:
    """Generate quiz questions from document collections using Gemini."""

    def __init__(self, api_key: str, chroma_path: str = "./chroma_db"):
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")

        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
        self.collection_manager = CollectionManager(chroma_path, embedding_fn)
        self.retriever = Retriever(self.collection_manager)
        self.quiz_cache = {}  # Store generated quizzes for answer checking

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def generate_quiz(
        self,
        collection_name: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        quiz_type: str = "mixed",
    ) -> dict:
        """
        Generate a quiz from a collection.

        Args:
            collection_name: Name of the document collection
            num_questions: Number of questions to generate (1-20)
            difficulty: "easy", "medium", or "hard"
            quiz_type: "mixed", "multiple_choice_only", or "true_false_only"

        Returns:
            Dictionary with:
            - quiz_id: Unique ID for this quiz
            - questions: List of generated questions
            - error: Error message if generation failed
        """
        try:
            # Step 1 — Retrieve context from collection
            context = self._get_quiz_context(collection_name, num_questions)

            if not context:
                return {
                    "error": "No relevant content found in the collection",
                    "questions": [],
                }

            # Step 2 — Build prompt for Gemini
            prompt = self._build_quiz_prompt(
                context, num_questions, difficulty, quiz_type
            )

            # Step 3 — Call Gemini
            logger.info(
                "Generating %d %s quiz questions from %s",
                num_questions,
                difficulty,
                collection_name,
            )
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text

            # Step 4 — Parse and validate JSON
            questions = self._parse_quiz_response(response_text, num_questions)

            if not questions:
                return {
                    "error": "Failed to parse quiz questions from AI response",
                    "questions": [],
                }

            # Step 5 — Generate quiz ID and cache for later answer checking
            quiz_id = str(uuid.uuid4())
            self.quiz_cache[quiz_id] = {
                "questions": questions,
                "collection": collection_name,
                "difficulty": difficulty,
                "quiz_type": quiz_type,
            }

            return {
                "quiz_id": quiz_id,
                "questions": questions,
                "error": None,
            }

        except Exception as e:
            logger.exception("Quiz generation failed for collection %s", collection_name)
            return {
                "error": f"Quiz generation failed: {str(e)}",
                "questions": [],
            }

    # ------------------------------------------------------------------
    # Answer checking
    # ------------------------------------------------------------------

    def check_answers(self, quiz_id: str, answers: list[dict]) -> dict:
        """
        Check user answers against the correct answers.

        Args:
            quiz_id: ID of the quiz
            answers: List of {"question_id": int, "user_answer": str|int}

        Returns:
            Dictionary with:
            - results: List of individual answer results
            - correct_count: Number of correct answers
            - score_percentage: Percentage score
            - error: Error message if check failed
        """
        try:
            # Get the cached quiz
            if quiz_id not in self.quiz_cache:
                return {
                    "error": f"Quiz {quiz_id} not found. Quiz data may have expired.",
                    "results": [],
                    "correct_count": 0,
                    "score_percentage": 0,
                }

            cached_quiz = self.quiz_cache[quiz_id]
            questions = cached_quiz["questions"]

            # Create a map of question_id to question
            questions_map = {q["question_id"]: q for q in questions}

            results = []
            correct_count = 0

            # Check each answer
            for answer in answers:
                question_id = answer["question_id"]
                user_answer = answer["user_answer"]

                if question_id not in questions_map:
                    logger.warning("Question %d not found in quiz %s", question_id, quiz_id)
                    continue

                question = questions_map[question_id]
                correct_answer = question.get("correct_answer")

                # Normalize answers for comparison
                is_correct = self._compare_answers(
                    user_answer, correct_answer, question.get("question_type")
                )

                if is_correct:
                    correct_count += 1

                result = {
                    "question_id": question_id,
                    "question_text": question["question_text"],
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "is_correct": is_correct,
                    "explanation": question.get("explanation", ""),
                    "question_type": question.get("question_type"),
                }
                results.append(result)

            total = len(results)
            score_percentage = (correct_count / total * 100) if total > 0 else 0

            return {
                "results": results,
                "correct_count": correct_count,
                "total_questions": total,
                "score_percentage": round(score_percentage, 1),
                "error": None,
            }

        except Exception as e:
            logger.exception("Answer checking failed for quiz %s", quiz_id)
            return {
                "error": f"Answer checking failed: {str(e)}",
                "results": [],
                "correct_count": 0,
                "score_percentage": 0,
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_quiz_context(self, collection_name: str, num_questions: int) -> str:
        """
        Retrieve relevant chunks to base quiz questions on.
        Gets more chunks for more questions.
        """
        top_k = min(num_questions * 3, 20)  # Scale up chunks based on questions needed
        chunks = self.retriever.search(
            question="main concepts important facts key ideas definitions",
            collection_name=collection_name,
            top_k=top_k,
        )

        if not chunks:
            return ""

        context_parts = []
        for chunk in chunks:
            context_parts.append(chunk.get("text", ""))

        return "\n\n".join(context_parts)

    def _build_quiz_prompt(
        self, context: str, num_questions: int, difficulty: str, quiz_type: str
    ) -> str:
        """Build the prompt for Gemini to generate quiz questions."""

        question_type_guidance = {
            "mixed": "Mix multiple choice, true/false, and short answer questions.",
            "multiple_choice_only": "Generate ONLY multiple choice questions with 4 options each.",
            "true_false_only": "Generate ONLY true/false questions.",
        }

        type_guidance = question_type_guidance.get(quiz_type, "Mix different types.")

        difficulty_guidance = {
            "easy": "Focus on straightforward facts and definitions. Questions should directly test understanding of main concepts.",
            "medium": "Mix factual recall with basic application and analysis questions.",
            "hard": "Include analysis, synthesis, and critical thinking questions. Avoid obvious answers.",
        }

        diff_guidance = difficulty_guidance.get(difficulty, "")

        prompt = f"""{_BASE_SYSTEM}

<TASK>
Generate exactly {num_questions} quiz questions based ONLY on the provided context.

Requirements:
- Generate exactly {num_questions} questions (no more, no fewer)
- Difficulty level: {difficulty}. {diff_guidance}
- Question mix: {type_guidance}
- For multiple choice: provide exactly 4 options
- For true/false: provide two options (True, False)
- Each question must be answerable from the context

Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
  "questions": [
    {{
      "question_id": 1,
      "question_text": "What is...",
      "question_type": "multiple_choice",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "explanation": "This is correct because..."
    }},
    {{
      "question_id": 2,
      "question_text": "True or False: ...",
      "question_type": "true_false",
      "options": ["True", "False"],
      "correct_answer": "True",
      "explanation": "According to the context..."
    }},
    {{
      "question_id": 3,
      "question_text": "Briefly explain...",
      "question_type": "short_answer",
      "correct_answer": "The answer should be: ...",
      "explanation": "This demonstrates understanding of..."
    }}
  ]
}}

CONTEXT:
{context}

Generate the quiz now. Return ONLY the JSON object, nothing else.
</TASK>"""

        return prompt

    def _parse_quiz_response(self, response_text: str, expected_count: int) -> list:
        """
        Parse and validate the JSON response from Gemini.
        Returns a list of validated question dictionaries.
        """
        try:
            # Try to extract JSON from the response (in case of markdown wrapping)
            text = response_text.strip()
            if text.startswith("```"):
                # Remove markdown code block if present
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            # Parse JSON
            data = json.loads(text)

            if not isinstance(data, dict) or "questions" not in data:
                logger.error("Invalid quiz response structure")
                return []

            questions = data["questions"]

            if not isinstance(questions, list):
                logger.error("Questions is not a list")
                return []

            if len(questions) != expected_count:
                logger.warning(
                    "Expected %d questions but got %d",
                    expected_count,
                    len(questions),
                )

            # Validate each question
            validated_questions = []
            for i, q in enumerate(questions):
                if self._validate_question(q):
                    validated_questions.append(q)
                else:
                    logger.warning("Question %d failed validation", i)

            return validated_questions

        except json.JSONDecodeError as e:
            logger.error("Failed to parse quiz JSON: %s", str(e))
            logger.debug("Response text: %s", response_text[:500])
            return []

    def _validate_question(self, question: dict) -> bool:
        """Validate that a question has all required fields."""
        required_fields = ["question_id", "question_text", "question_type", "correct_answer"]

        for field in required_fields:
            if field not in question:
                logger.warning("Question missing required field: %s", field)
                return False

        # Validate question_type
        valid_types = ["multiple_choice", "true_false", "short_answer"]
        if question["question_type"] not in valid_types:
            logger.warning(
                "Invalid question_type: %s", question.get("question_type")
            )
            return False

        # For multiple choice, validate options
        if question["question_type"] == "multiple_choice":
            if "options" not in question or not isinstance(question["options"], list):
                logger.warning("Multiple choice question missing options")
                return False
            if len(question["options"]) < 2:
                logger.warning("Multiple choice question has fewer than 2 options")
                return False

        return True

    def _compare_answers(self, user_answer, correct_answer, question_type: str) -> bool:
        """
        Compare user answer with correct answer, accounting for question type.
        """
        if question_type in ["multiple_choice", "true_false"]:
            # For multiple choice and true/false, do exact string comparison
            return str(user_answer).strip().lower() == str(correct_answer).strip().lower()

        if question_type == "short_answer":
            # For short answers, do a looser comparison
            # Check if key words from correct answer appear in user answer
            user_words = set(str(user_answer).lower().split())
            correct_words = set(str(correct_answer).lower().split())

            # If user answer contains most key words, consider it correct
            # (This is a simple heuristic; in production you might use an LLM for this)
            common_words = user_words.intersection(correct_words)
            required_match = len(correct_words) * 0.6  # 60% of words should match

            return len(common_words) >= required_match

        return False
