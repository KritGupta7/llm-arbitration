import json
from app.services.openai_client import client
from app.models.critique import Critique


def evaluate_accuracy(question: str, answer: str) -> Critique:
    prompt = f"""You are a factual accuracy critic. Your job is to evaluate whether the answer contains correct, verifiable facts.

Question:
{question}

Answer:
{answer}

Return ONLY valid JSON. No markdown, no code fences, no extra text. The JSON must match this exact structure:

{{
  "dimension": "accuracy",
  "score": 3,
  "confidence": 0.85,
  "issues": [
    {{
      "quote": "exact phrase from the answer that is wrong",
      "problem": "why this specific phrase is factually incorrect",
      "severity": 4
    }}
  ],
  "explanation": "overall explanation of the accuracy evaluation"
}}

Rules:
- score: integer 1 (very inaccurate) to 5 (fully accurate)
- confidence: float 0.0 to 1.0 representing how confident you are in this evaluation
- issues: list of factual errors found; empty list [] if none
- severity per issue: integer 1 (minor) to 5 (critical)
- quote must be a verbatim excerpt from the answer
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
            f"accuracy critic returned invalid JSON: {exc}\nRaw content: {content}"
        ) from exc

    return Critique(**data)
