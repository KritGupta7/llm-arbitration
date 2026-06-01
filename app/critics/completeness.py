import json
from app.services.openai_client import client
from app.models.critique import Critique


def evaluate_completeness(question: str, answer: str) -> Critique:
    prompt = f"""
You are a completeness critic.

Evaluate whether the answer fully addresses the user's question.
Check if any important parts are missing or incomplete.

Question:
{question}

Answer:
{answer}

Return ONLY valid JSON in this exact format:
{{
  "score": 1,
  "issue": "main completeness issue",
  "explanation": "short explanation"
}}

Score must be from 1 to 5.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content
    data = json.loads(content)

    return Critique(**data)