import asyncio

from app.critics.accuracy import evaluate_accuracy
from app.critics.logic import evaluate_logic
from app.critics.completeness import evaluate_completeness
from app.adjudicator import adjudicate


async def run_arbitration(question: str, answer: str):
    accuracy_task = asyncio.to_thread(evaluate_accuracy, question, answer)
    logic_task = asyncio.to_thread(evaluate_logic, question, answer)
    completeness_task = asyncio.to_thread(evaluate_completeness, question, answer)

    accuracy, logic, completeness = await asyncio.gather(
        accuracy_task,
        logic_task,
        completeness_task
    )

    verdict = adjudicate(accuracy, logic, completeness)

    print(verdict.model_dump_json(indent=2))


if __name__ == "__main__":
    question = input("Enter the original question: ")
    answer = input("Enter the LLM answer to evaluate: ")

    asyncio.run(run_arbitration(question, answer))