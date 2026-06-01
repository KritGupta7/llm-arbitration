import json
from app.services.openai_client import client
from app.models.critique import Critique


def evaluate_logic(question: str, answer: str) -> Critique:
    prompt = f"""
You are a logical consistency critic.

Evaluate whether the answer's reasoning is logically consistent and whether the conclusion follows from the explanation.

Question:
{question}

Answer:
{answer}

Return ONLY valid JSON in this exact format:
{{
  "score": 1,
  "issue": "main logical issue",
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
    