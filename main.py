import asyncio

from app.arbitration import arbitrate


if __name__ == "__main__":
    question = input("Enter the original question: ")
    answer = input("Enter the LLM answer to evaluate: ")

    verdict = asyncio.run(arbitrate(question, answer))

    print(verdict.model_dump_json(indent=2))