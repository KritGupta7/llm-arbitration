import json
from app.services.openai_client import client
from app.models.critique import Critique


def evaluate_completeness(question: str, answer: str) -> Critique:
    prompt = f"""You are a completeness critic. Your job is to evaluate whether the answer adequately addresses what the question actually asked for.

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
- score: integer 1 (fails to address the question) to 5 (fully addresses what was asked)
- confidence: float 0.0 to 1.0 representing how confident you are in this evaluation
- CRITICAL DISTINCTION — you must classify every potential gap as one of:
  - REQUIRED: the question explicitly asked for this information, or the answer is unusable without it
  - OPTIONAL: this is useful background, extra detail, or advanced context that goes beyond what the question asked
- Only REQUIRED gaps belong in issues. Do NOT add optional gaps as issues.
- severity calibration (follow this strictly):
  - severity 5: the answer completely fails to address the core of the question
  - severity 4: the answer addresses the question but omits information the question specifically asked for
  - severity 3: the answer is mostly complete but leaves out something that would genuinely help the reader understand
  - severity 2: the answer could be slightly expanded but is adequate as-is
  - severity 1: minor omission of background detail that the question did not ask for
- Scoring guidance:
  - score 5: the answer directly and correctly addresses everything the question asked for
  - score 4: the answer is mostly complete with only minor optional details missing
  - score 3: the answer addresses the question but is noticeably thin or missing something helpful
  - score 2: the answer is partially relevant but misses a significant part of what was asked
  - score 1: the answer barely or does not address the question
- A concise correct answer to a simple question MUST score 4 or 5. Do not penalize brevity.
- Advanced topics, edge cases, and extra context that the question did not ask for should NOT lower the score below 4.
- quote must be a verbatim excerpt from the answer; if the gap is a fully missing topic, use the most relevant existing phrase as anchor
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
