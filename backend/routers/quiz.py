"""
Quiz router — Handle quiz generation and answer checking endpoints.

Endpoints:
- POST /quiz/generate — Generate a quiz from a collection
- POST /quiz/check-answers — Check answers and return results
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from schemas import (
    QuizGenerationRequest,
    QuizGenerationResponse,
    QuizAnswerRequest,
    QuizResultResponse,
)
from services.input_guard import validate_collection_name, InputValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


def get_quiz_generator():
    """
    Import here (not at module level) to avoid circular imports
    when main.py registers this router before quiz_generator is created.
    """
    from main import quiz_generator
    return quiz_generator


@router.post("/quiz/generate", response_model=QuizGenerationResponse)
def generate_quiz(request: QuizGenerationRequest):
    """
    Generate a quiz from a document collection.

    Parameters:
    - collection: Name of the collection to generate quiz from
    - num_questions: Number of questions (1-20, default 5)
    - difficulty: "easy", "medium", "hard" (default "medium")
    - quiz_type: "mixed", "multiple_choice_only", "true_false_only" (default "mixed")

    Returns:
    - quiz_id: Unique ID for this quiz (use for answer checking)
    - questions: List of generated quiz questions
    """
    try:
        clean_collection = validate_collection_name(request.collection)
    except InputValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info(
        "Quiz generation requested — collection: %s | num_questions: %d | difficulty: %s",
        clean_collection,
        request.num_questions,
        request.difficulty,
    )

    try:
        result = get_quiz_generator().generate_quiz(
            collection_name=clean_collection,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            quiz_type=request.quiz_type,
        )

        if result.get("error"):
            logger.warning("Quiz generation failed: %s", result["error"])
            return JSONResponse(
                status_code=400,
                content={
                    "quiz_id": None,
                    "collection": clean_collection,
                    "questions": [],
                    "num_questions": request.num_questions,
                    "difficulty": request.difficulty,
                    "quiz_type": request.quiz_type,
                    "error": result["error"],
                },
            )

        logger.info(
            "Quiz generated successfully — quiz_id: %s | questions: %d",
            result.get("quiz_id"),
            len(result.get("questions", [])),
        )

        return JSONResponse(
            status_code=200,
            content={
                "quiz_id": result.get("quiz_id"),
                "collection": clean_collection,
                "questions": result.get("questions", []),
                "num_questions": request.num_questions,
                "difficulty": request.difficulty,
                "quiz_type": request.quiz_type,
                "error": None,
            },
        )

    except Exception:
        logger.exception("Quiz generation processing failed for collection %s", clean_collection)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating the quiz. Please try again.",
        )


@router.post("/quiz/check-answers", response_model=QuizResultResponse)
def check_answers(request: QuizAnswerRequest):
    """
    Check user answers against the correct answers.

    Parameters:
    - quiz_id: The ID returned from /quiz/generate
    - answers: List of {"question_id": int, "user_answer": str|int}

    Returns:
    - results: Detailed results for each question
    - correct_count: Number of correct answers
    - score_percentage: Percentage score (0-100)
    - total_questions: Total number of questions
    """
    logger.info(
        "Answer checking requested — quiz_id: %s | answers_submitted: %d",
        request.quiz_id,
        len(request.answers),
    )

    try:
        # Convert answers to list of dicts for the service
        answers_list = [
            {"question_id": a.question_id, "user_answer": a.user_answer}
            for a in request.answers
        ]

        result = get_quiz_generator().check_answers(
            quiz_id=request.quiz_id,
            answers=answers_list,
        )

        if result.get("error"):
            logger.warning("Answer checking failed: %s", result["error"])
            return JSONResponse(
                status_code=400,
                content={
                    "quiz_id": request.quiz_id,
                    "total_questions": 0,
                    "correct_count": 0,
                    "score_percentage": 0,
                    "results": [],
                    "error": result["error"],
                },
            )

        logger.info(
            "Answer checking complete — quiz_id: %s | score: %.1f%%",
            request.quiz_id,
            result.get("score_percentage", 0),
        )

        return JSONResponse(
            status_code=200,
            content={
                "quiz_id": request.quiz_id,
                "total_questions": result.get("total_questions", 0),
                "correct_count": result.get("correct_count", 0),
                "score_percentage": result.get("score_percentage", 0),
                "results": result.get("results", []),
                "error": None,
            },
        )

    except Exception:
        logger.exception("Answer checking processing failed for quiz %s", request.quiz_id)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while checking your answers. Please try again.",
        )
