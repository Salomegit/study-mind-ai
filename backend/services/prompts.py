"""
Prompt templates and question classification for RAG answer generation.

This module handles:
- Question type classification (factual, definition, summary, etc.)
- Prompt template routing based on question type and confidence
- LLM instruction customization per user type (KCSE, university, researcher)
"""

# Low confidence threshold — if best match is below this, use low confidence prompt
LOW_CONFIDENCE_THRESHOLD = 0.30


# ------------------------------------------------------------------
# Question Classification
# ------------------------------------------------------------------

def classify_question(question: str) -> str:
    """
    Classify the question type to route to the appropriate prompt template.
    Returns one of: 'research', 'compare', 'summary', 'explanation', 'definition', 'factual'

    Args:
        question: The user's question string

    Returns:
        str: Question type category
    """
    q = question.lower()

    summary_keywords = [
        'summarise', 'summarize', 'key points', 'main points',
        'overview', 'chapter', 'outline', 'briefly', 'abstract'
    ]
    explain_keywords = [
        'explain', 'how does', 'how do', 'why does',
        'walk me through', 'break down', 'elaborate'
    ]
    compare_keywords = [
        'compare', 'difference', 'versus', 'vs', 'contrast',
        'similarities', 'distinguish between'
    ]
    research_keywords = [
        'methodology', 'hypothesis', 'literature', 'findings',
        'argue', 'critique', 'evaluate', 'evidence', 'theory',
        'framework', 'gap', 'limitations', 'implications'
    ]
    definition_keywords = [
        'define', 'what is', 'what are', 'meaning of',
        'concept of', 'term'
    ]

    if any(k in q for k in research_keywords):
        return 'research'
    if any(k in q for k in compare_keywords):
        return 'compare'
    if any(k in q for k in summary_keywords):
        return 'summary'
    if any(k in q for k in explain_keywords):
        return 'explanation'
    if any(k in q for k in definition_keywords):
        return 'definition'
    return 'factual'


# ------------------------------------------------------------------
# Prompt Templates — Tailored by Question Type
# ------------------------------------------------------------------

FACTUAL_PROMPT = """You are a precise study assistant.
Using ONLY the context below, answer the question directly and accurately.
Cite which part of the context supports your answer.

Context:
{context}

Student question (answer only from the context above): {question}

Give a clear, direct answer in 2-4 sentences."""

DEFINITION_PROMPT = """You are a knowledgeable study assistant serving students,
university learners, and researchers.
Using the context below, provide a clear definition of the term or concept asked about.
Include any nuance or academic precision present in the source material.

Context:
{context}

Term to define (use only the context above): {question}

Provide: a concise definition, then any important distinctions or academic usage
noted in the context."""

SUMMARY_PROMPT = """You are a study assistant helping someone review material.
Summarise the main ideas from the context below into clear, structured points.
Preserve technical terms and academic language where present —
this may be used by a university student or researcher.

Context:
{context}

Request (summarise only what is in the context above): {question}

Respond with:
- 4-6 bullet points of the key ideas
- One sentence noting what topic area this covers"""

EXPLANATION_PROMPT = """You are a patient and knowledgeable tutor.
Use the context below to explain the concept clearly.
Adapt your depth: if the source material is academic or technical,
preserve that depth — do not oversimplify for a researcher or thesis student.

Context:
{context}

Concept to explain (use only the context above): {question}

Structure your answer as:
1. Core idea in one sentence
2. Step-by-step breakdown
3. Why it matters (if mentioned in context)"""

COMPARE_PROMPT = """You are an analytical study assistant.
Using the context below, compare and contrast the concepts or items in the question.
Maintain academic rigour — this may be for an essay, thesis, or research paper.

Context:
{context}

Comparison request (use only the context above): {question}

Structure your answer as:
- Similarities: ...
- Differences: ...
- Key insight: one sentence on what the comparison reveals"""

RESEARCH_PROMPT = """You are an academic research assistant with expertise in
critical analysis. The user may be a researcher, postgraduate, or thesis student.
Using the context below, engage with the question at an appropriately academic level.
Reference specific parts of the context to support your analysis.
Do not simplify unnecessarily — precision and nuance matter here.

Context:
{context}

Research question (analyse using only the context above): {question}

Provide a structured academic response. Where the context supports it,
note evidence, counter-arguments, or gaps."""

LOW_CONFIDENCE_PROMPT = """You are a helpful study assistant.
The retrieved context may not perfectly match the question.
Use whatever relevant information exists. Be honest about what the context covers.
Do not fabricate information not present in the context.

Context:
{context}

Question (answer as best as you can from the context above): {question}

If the context is insufficient, tell the user:
- What the context does cover
- What specific term or topic they should search for instead"""

PROMPT_MAP = {
    'factual':     FACTUAL_PROMPT,
    'definition':  DEFINITION_PROMPT,
    'summary':     SUMMARY_PROMPT,
    'explanation': EXPLANATION_PROMPT,
    'compare':     COMPARE_PROMPT,
    'research':    RESEARCH_PROMPT,
}


# ------------------------------------------------------------------
# Prompt Builder
# ------------------------------------------------------------------

def build_prompt(question: str, context: str, best_score: float) -> str:
    """
    Route to the appropriate prompt template based on question type and confidence.

    Intelligently selects a prompt instruction based on:
    - How well the retrieved context matches the question (best_score)
    - What type of question is being asked (classification)

    Args:
        question:   The user's question
        context:    The retrieved document context
        best_score: The similarity score of the best match (0.0 to 1.0)

    Returns:
        str: A formatted prompt string ready for Gemini
    """
    if best_score < LOW_CONFIDENCE_THRESHOLD:
        template = LOW_CONFIDENCE_PROMPT
    else:
        qtype = classify_question(question)
        template = PROMPT_MAP[qtype]

    return template.format(context=context, question=question)
