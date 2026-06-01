from app.services.openai_client import client


def evaluate_accuracy(question: str, answer: str) -> str:
    prompt = f"""
You are a factual accuracy critic.

Your job is to evaluate whether the answer is factually correct.

Question:
{question}

Answer:
{answer}

Return your evaluation in this format:

Score: <1-5>
Issue: <main factual issue>
Explanation: <short explanation>
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content