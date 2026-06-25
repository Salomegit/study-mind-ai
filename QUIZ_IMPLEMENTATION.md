# Week 4: Quiz Generation Feature - Implementation Guide

## Overview

The Week 4 Quiz Generation feature enables users to:
1. **Generate quizzes** from their uploaded document collections
2. **Take interactive quizzes** with multiple question types
3. **Check answers** and receive detailed feedback
4. **View detailed results** with explanations

The system uses Google's Gemini LLM to generate questions and validate answers, with full JSON parsing and validation.

---

## Architecture

### Backend Stack
- **Framework**: FastAPI (Python)
- **LLM**: Google Gemini API (gemini-2.5-flash)
- **Vector Store**: ChromaDB (for document retrieval)
- **Validation**: Pydantic schemas

### Frontend Stack
- **Framework**: Next.js (TypeScript)
- **Styling**: Tailwind CSS + custom theme
- **Animations**: Framer Motion
- **State Management**: React hooks (useQuiz)

---

## API Endpoints

### 1. Generate Quiz
```http
POST /quiz/generate
Content-Type: application/json

{
  "collection": "Biology",
  "num_questions": 5,
  "difficulty": "medium",
  "quiz_type": "mixed"
}
```

**Response** (200 OK):
```json
{
  "quiz_id": "uuid-string",
  "collection": "Biology",
  "questions": [
    {
      "question_id": 1,
      "question_text": "What is...",
      "question_type": "multiple_choice",
      "options": ["A", "B", "C", "D"],
      "explanation": "The correct answer is..."
    }
  ],
  "num_questions": 5,
  "difficulty": "medium",
  "quiz_type": "mixed",
  "error": null
}
```

### 2. Check Answers
```http
POST /quiz/check-answers
Content-Type: application/json

{
  "quiz_id": "uuid-string",
  "answers": [
    {"question_id": 1, "user_answer": "A"},
    {"question_id": 2, "user_answer": true}
  ]
}
```

**Response** (200 OK):
```json
{
  "quiz_id": "uuid-string",
  "total_questions": 2,
  "correct_count": 1,
  "score_percentage": 50.0,
  "results": [
    {
      "question_id": 1,
      "question_text": "What is...",
      "user_answer": "A",
      "correct_answer": "A",
      "is_correct": true,
      "explanation": "...",
      "question_type": "multiple_choice"
    }
  ],
  "error": null
}
```

### 3. List Collections
```http
GET /collections
```

**Response** (200 OK):
```json
{
  "collections": ["Biology", "History", "Physics"]
}
```

---

## Features

### Question Types

#### 1. Multiple Choice
- 4 options provided
- User selects one
- Exact string matching (case-insensitive)
- Example: MCQ about biology definitions

#### 2. True/False
- 2 boolean options
- User picks True or False
- Case-insensitive comparison
- Quick knowledge assessment

#### 3. Short Answer
- Free-text response
- Fuzzy matching (60% word overlap required)
- Better for deeper understanding
- Example: "Explain photosynthesis"

### Difficulty Levels

| Level | Characteristics |
|-------|-----------------|
| **Easy** | Straightforward facts, definitions, direct recall |
| **Medium** | Mix of factual recall and basic application |
| **Hard** | Analysis, synthesis, critical thinking |

### Quiz Types

| Type | Description |
|------|-------------|
| **Mixed** | Combination of all three question types |
| **Multiple Choice Only** | Only MCQ questions |
| **True/False Only** | Only T/F questions |

---

## Installation & Setup

### Backend Requirements

1. **Install dependencies**:
```bash
cd backend
source myvenv/bin/activate
pip install -r requirements.txt
```

2. **Set environment variables** (`.env`):
```env
GEMINI_API_KEY=your_api_key_here
CHROMA_DB_PATH=./chroma_db
DEBUG=false
```

3. **Start backend**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Requirements

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Set environment variables** (`.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **Start frontend**:
```bash
npm run dev
```

4. **Access**: http://localhost:3000/quiz

---

## How It Works

### Quiz Generation Flow

```
1. User selects collection & parameters
   ↓
2. Frontend calls /quiz/generate
   ↓
3. Backend retrieves relevant chunks from ChromaDB
   ↓
4. Builds prompt with difficulty & type guidelines
   ↓
5. Calls Gemini to generate questions
   ↓
6. Parses JSON response (with markdown unwrapping)
   ↓
7. Validates all questions
   ↓
8. Caches quiz in memory with quiz_id
   ↓
9. Returns questions to frontend
```

### Answer Checking Flow

```
1. User submits answers after all questions
   ↓
2. Frontend calls /quiz/check-answers with quiz_id & answers
   ↓
3. Backend retrieves cached quiz
   ↓
4. Compares each answer (type-aware):
   - MCQ/T/F: Exact match
   - Short answer: Fuzzy match
   ↓
5. Calculates score percentage
   ↓
6. Returns detailed results with explanations
   ↓
7. Frontend displays score & breakdown
```

---

## Code Organization

### Backend

```
backend/
├── schemas.py              # Pydantic models (quiz-related)
├── services/
│   └── quiz.py            # QuizGenerator class & logic
├── routers/
│   ├── quiz.py            # Quiz endpoints
│   └── collections.py     # Added list_collections endpoint
└── main.py                # Integrated quiz router
```

### Frontend

```
frontend/
├── app/
│   └── quiz/
│       └── page.tsx       # Main quiz page
├── components/
│   ├── quiz/
│   │   ├── QuestionCard.tsx    # Question display
│   │   ├── QuizResults.tsx     # Results screen
│   │   └── QuizSetup.tsx       # Setup form
│   └── Navbar.tsx         # Added Quiz link
├── hooks/
│   └── useQuiz.ts         # Quiz state hook
└── lib/api/
    └── quiz.ts            # API client
```

---

## Key Implementation Details

### JSON Parsing

The quiz service handles various JSON response formats from Gemini:
- Unwraps markdown code blocks (``​`json...`​``)
- Validates response structure
- Validates each question's required fields
- Logs parsing errors for debugging

### Answer Comparison

**Multiple Choice & True/False**:
```python
str(user_answer).strip().lower() == str(correct_answer).strip().lower()
```

**Short Answer** (Fuzzy):
```python
# Requires 60% word overlap between user and correct answer
common_words = user_words.intersection(correct_words)
required_match = len(correct_words) * 0.6
return len(common_words) >= required_match
```

### Quiz Caching

Quizzes are stored in memory with a UUID:
```python
self.quiz_cache[quiz_id] = {
  "questions": [...],
  "collection": "...",
  "difficulty": "...",
  "quiz_type": "..."
}
```

⚠️ **Note**: Cache is cleared on server restart. For production, use persistent storage (Redis, database).

---

## Prompting Strategy

The backend uses structured prompts with:

1. **System block** (`<SYSTEM>`): Base instruction set
2. **Task block** (`<TASK>`): Specific requirements
3. **Context block** (`<CONTEXT>`): Document excerpts
4. **JSON format specification**: Exact output structure expected

Example:
```
<SYSTEM>
You are an educational quiz generator...
</SYSTEM>

<TASK>
Generate exactly 5 medium difficulty mixed questions.
[Format requirements...]
</TASK>

<CONTEXT>
[Document chunks here]
</CONTEXT>
```

---

## Error Handling

### Frontend

| Error | Handling |
|-------|----------|
| No collections | Show empty state with upload link |
| Generation failed | Display error message, allow retry |
| Network error | Show error toast |
| Invalid answers | Prevent submit, show validation message |

### Backend

| Error | Response |
|-------|----------|
| Invalid collection | 422 Unprocessable Entity |
| JSON parse failure | 400 Bad Request with error description |
| Quiz not found | 400 Bad Request (expired cache) |
| Server error | 500 Internal Server Error |

---

## Testing Checklist

- [ ] Generate quiz with 5 questions
- [ ] Generate quiz with different difficulty levels
- [ ] Generate quiz with different question types
- [ ] Navigate between questions
- [ ] Submit incomplete quiz (should show validation)
- [ ] Submit complete quiz
- [ ] Check all question types are scored correctly
- [ ] Verify score percentage calculation
- [ ] Test with different collections
- [ ] Test error states (no collections, network errors)

---

## Performance Considerations

### Optimization

1. **Chunk retrieval**: Gets 3x questions worth of chunks (efficient context)
2. **Prompt engineering**: Clear, structured prompts reduce parsing errors
3. **Caching**: Quiz cache avoids re-computation on answer checking
4. **Validation**: Early validation prevents wasted processing

### Scaling

For production deployments:
1. Replace in-memory cache with Redis or database
2. Implement quiz expiration (e.g., 24 hours)
3. Add rate limiting on quiz generation
4. Consider quiz generation queuing (async processing)
5. Log all quiz generation for analytics

---

## Security Notes

### Input Validation

- Collection names sanitized via `sanitise_collection_name()`
- Number of questions limited to 1-20
- Difficulty & quiz_type enum validation
- Quiz ID format validation (UUID)

### API Security

- CORS configured for localhost:3000 only
- No secrets in responses
- Error messages sanitized (no stack traces)
- All Pydantic models validate input

---

## Future Enhancements

1. **LLM-based answer checking**: Use Gemini for fuzzy short answer validation
2. **Question difficulty auto-detection**: Analyze content complexity
3. **Quiz history**: Store quizzes with timestamps
4. **Analytics**: Track user performance trends
5. **Custom rubrics**: Allow users to set grading criteria
6. **Collaborative quizzes**: Share quizzes between users
7. **Question bank**: Reuse questions across sessions
8. **Adaptive difficulty**: Adjust difficulty based on performance

---

## Troubleshooting

### Quiz generation times out
- **Cause**: Large collection or slow LLM response
- **Fix**: Reduce `num_questions`, check Gemini API quota

### Answers not checking correctly
- **Cause**: Answer format mismatch
- **Fix**: Verify question_id, ensure answers match option strings

### Collections not loading
- **Cause**: No collections uploaded or API error
- **Fix**: Check if documents were uploaded, verify backend is running

### "Quiz not found" error
- **Cause**: Cache expired or server restarted
- **Fix**: Regenerate quiz (quiz cache cleared on restart)

---

## References

- [Gemini API Documentation](https://ai.google.dev/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
