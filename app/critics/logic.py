import json
from app.services.openai_client import client
from app.models.critique import Critique


def evaluate_logic(question: str, answer: str) -> Critique:
    prompt = f"""You are a logical consistency critic. Your job is to evaluate whether the reasoning and claims in the answer are coherent, non-contradictory, and internally consistent.

Question:
{question}

Answer:
{answer}

Return ONLY valid JSON. No markdown, no code fences, no extra text. The JSON must match this exact structure:

{{
  "dimension": "logic",
  "score": 3,
  "confidence": 0.85,
  "issues": [
    {{
      "quote": "exact phrase from the answer that is logically flawed",
      "problem": "why this specific phrase is logically inconsistent or contradictory",
      "severity": 4
    }}
  ],
  "explanation": "overall explanation of the logical consistency evaluation"
}}

Rules:
- score: integer 1 (deeply incoherent) to 5 (perfectly logical)
- confidence: float 0.0 to 1.0 representing how confident you are in this evaluation
- issues: list of logical flaws found; empty list [] if none
- severity calibration (follow this strictly):
  - severity 5: the answer directly contradicts itself or its conclusion is the opposite of what the reasoning supports
  - severity 4: there is a clear logical non-sequitur or the answer makes a claim that contradicts another claim it makes
  - severity 3: the reasoning is loose or somewhat circular, but not outright wrong
  - severity 2: a minor imprecision in how the logic is expressed
  - severity 1: a trivial phrasing issue that does not affect the reasoning
- DO NOT penalize for brevity. A concise answer can be perfectly logical.
- DO NOT penalize for not including additional reasoning steps that were not required by the question.
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
            f"logic critic returned invalid JSON: {exc}\nRaw content: {content}"
        ) from exc

    return Critique(**data)
