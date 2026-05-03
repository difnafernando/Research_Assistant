"""
tools.py — Tool Router for the Research Agent

This module detects what kind of task the user is asking for,
selects the right "tool" (prompt augmentation), and returns
enriched context to the agent.

Tools available:
  - concept_explainer   : Breaks down complex ideas
  - quiz_generator      : Generates practice questions
  - paper_summarizer    : Summarizes academic content
  - analogy_builder     : Creates intuitive analogies
  - math_helper         : Handles equations and proofs
  - code_explainer      : Explains code / algorithms
  - study_planner       : Creates structured study plans
  - debate_analyzer     : Analyzes both sides of an argument
"""

import re
from typing import Tuple, Optional


# ── Keyword maps for tool detection ──────────────────────────────────────────
TOOL_PATTERNS = {
    "math_helper": [
        r"\b(equation|formula|proof|theorem|integral|derivative|matrix|vector|calculus|algebra|statistics|probability|solve|calculate)\b"
    ],
    "code_explainer": [
        r"\b(code|algorithm|function|program|python|java|c\+\+|implementation|complexity|big[- ]o|pseudocode|debug)\b"
    ],
    "paper_summarizer": [
        r"\b(paper|research|study|abstract|literature|journal|publication|arxiv|findings|methodology)\b"
    ],
    "analogy_builder": [
        r"\b(analogy|intuition|explain.*simple|simple.*explain|like.*real life|metaphor|dumb it down|eli5)\b"
    ],
    "study_planner": [
        r"\b(study plan|schedule|revision|exam|prepare|roadmap|how to learn|learning path|curriculum)\b"
    ],
    "quiz_generator": [
        r"\b(quiz|test|exam|question|practice|assess|flashcard)\b"
    ],
    "debate_analyzer": [
        r"\b(pros|cons|advantage|disadvantage|compare|versus|vs\.?|debate|argument|critique|limitation|weakness)\b"
    ],
    "concept_explainer": [
        r"\b(what is|what are|explain|define|meaning|how does|how do|why is|why does|describe)\b"
    ],
}

TOOL_CONTEXT = {
    "math_helper": """[MATH TOOL ACTIVE]
- Show step-by-step working for all calculations
- Use LaTeX-style notation where helpful (e.g. x² + 2x + 1)
- Explain the intuition BEFORE the math
- Call out common mistakes
- Verify units and dimensions""",

    "code_explainer": """[CODE TOOL ACTIVE]
- Explain what each part of the code does
- Analyze time/space complexity (Big-O)
- Suggest optimizations if possible
- Use comments in any code you write
- Compare with alternative approaches""",

    "paper_summarizer": """[PAPER SUMMARIZER ACTIVE]
- Structure: Background → Method → Results → Impact
- Highlight the key contribution / novelty
- Identify limitations the authors mention
- Note the dataset / evaluation used
- Suggest 2-3 related works to explore""",

    "analogy_builder": """[ANALOGY TOOL ACTIVE]
- Lead with a vivid, memorable everyday analogy
- Build from the analogy to the actual concept
- Use multiple analogies if the first doesn't land
- Avoid technical jargon until the intuition is clear
- End with a one-liner the student can repeat to others""",

    "study_planner": """[STUDY PLANNER ACTIVE]
- Ask about the time available and current knowledge level
- Break the topic into modules/milestones
- Suggest resources (textbooks, courses, papers) per module
- Include active recall and spaced repetition tips
- Provide a realistic weekly schedule template""",

    "quiz_generator": """[QUIZ TOOL ACTIVE]
- Generate 3–5 questions across difficulty levels
- Mix question types: MCQ, short answer, application
- After user responds, score and give detailed feedback
- Identify specific knowledge gaps
- Suggest what to review based on answers""",

    "debate_analyzer": """[DEBATE ANALYZER ACTIVE]
- Present both sides with equal intellectual rigour
- Use real-world evidence for each side
- Identify hidden assumptions in each argument
- Note when empirical data resolves the debate
- Conclude with a nuanced, balanced verdict""",

    "concept_explainer": """[CONCEPT EXPLAINER ACTIVE]
- Definition → Analogy → Example → Application
- Explain why this concept matters
- Connect to related concepts the student might know
- Highlight common misconceptions
- End with a memorable one-liner summary""",
}

TOOL_LABELS = {
    "math_helper":       "Math Solver",
    "code_explainer":    "Code Analyzer",
    "paper_summarizer":  "Paper Summarizer",
    "analogy_builder":   "Analogy Builder",
    "study_planner":     "Study Planner",
    "quiz_generator":    "Quiz Generator",
    "debate_analyzer":   "Debate Analyzer",
    "concept_explainer": "Concept Explainer",
}

# Mode → preferred tool
MODE_DEFAULT_TOOL = {
    "Research":  "concept_explainer",
    "Explain":   "analogy_builder",
    "Quiz Me":   "quiz_generator",
    "Summarize": "paper_summarizer",
    "Critique":  "debate_analyzer",
}


def detect_tool(user_input: str) -> Optional[str]:
    """
    Detect which tool to use based on keywords in the user's message.
    Returns a tool name or None.
    """
    text = user_input.lower()
    for tool, patterns in TOOL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return tool
    return None


def get_tool_response(user_input: str, mode: str) -> Tuple[str, str]:
    """
    Main tool router.
    Returns: (tool_label, tool_context_string)
    """
    # 1. Try to detect from user message
    tool = detect_tool(user_input)

    # 2. Fall back to mode default
    if not tool:
        tool = MODE_DEFAULT_TOOL.get(mode, "concept_explainer")

    label = TOOL_LABELS.get(tool, "Research Assistant")
    context = TOOL_CONTEXT.get(tool, "")

    return label, context
