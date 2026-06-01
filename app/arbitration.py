import asyncio

from app.critics.accuracy import evaluate_accuracy
from app.critics.logic import evaluate_logic
from app.critics.completeness import evaluate_completeness
from app.adjudicator import adjudicate
from app.models.arbitration_result import ArbitrationResult


async def arbitrate(question: str, answer: str) -> ArbitrationResult:
    accuracy_task = asyncio.to_thread(evaluate_accuracy, question, answer)
    logic_task = asyncio.to_thread(evaluate_logic, question, answer)
    completeness_task = asyncio.to_thread(evaluate_completeness, question, answer)

    accuracy, logic, completeness = await asyncio.gather(
        accuracy_task,
        logic_task,
        completeness_task
    )

    return adjudicate(accuracy, logic, completeness)