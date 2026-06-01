import json
from app.services.openai_client import client
from app.models.critique import Critique


def evaluate_accuracy(question: str, answer: str) -> Critique:
    prompt = f"""
You are a factual accuracy critic.

Evaluate the answer for factual correctness.

Question:
{question}

Answer:
{answer}

Return ONLY valid JSON in this exact format:
{{
  "score": 1,
  "issue": "main factual issue",
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