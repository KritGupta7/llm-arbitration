import json
from app.services.openai_client import client
from app.models.critique import Critique


def evaluate_completeness(question: str, answer: str) -> Critique:
    prompt = f"""You are a completeness critic. Your job is to evaluate whether the answer fully addresses the question, covering all important aspects without omitting key information.

Question:
{question}

Answer:
{answer}

Return ONLY valid JSON. No markdown, no code fences, no extra text. The JSON must match this exact structure:

{{
  "dimension": "completeness",
  "score": 3,
  "confidence": 0.85,
  "issues": [
    {{
      "quote": "exact phrase from the answer that is incomplete or missing context",
      "problem": "what important information is missing or insufficiently addressed",
      "severity": 4
    }}
  ],
  "explanation": "overall explanation of the completeness evaluation"
}}

Rules:
- score: integer 1 (very incomplete) to 5 (fully complete)
- confidence: float 0.0 to 1.0 representing how confident you are in this evaluation
- issues: list of omissions or gaps found; empty list [] if none
- severity per issue: integer 1 (minor gap) to 5 (critical omission)
- quote must be a verbatim excerpt from the answer; if the issue is a missing topic entirely, use a representative phrase from the answer as the anchor
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content.strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"completeness critic returned invalid JSON: {exc}\nRaw content: {content}"
        ) from exc

    return Critique(**data)
