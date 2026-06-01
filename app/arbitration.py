import asyncio
from typing import Callable

from app.critics.accuracy import evaluate_accuracy
from app.critics.logic import evaluate_logic
from app.critics.completeness import evaluate_completeness
from app.adjudicator import adjudicate
from app.models.critique import Critique
from app.models.arbitration_result import ArbitrationResult


def _run_critic_safely(
    name: str,
    critic_func: Callable[[str, str], Critique],
    question: str,
    answer: str,
) -> tuple[str, Critique | None, str | None]:
    try:
        critique = critic_func(question, answer)
        return (name, critique, None)
    except Exception as exc:
        return (name, None, str(exc))


async def arbitrate(question: str, answer: str) -> ArbitrationResult:
    results = await asyncio.gather(
        asyncio.to_thread(_run_critic_safely, "accuracy", evaluate_accuracy, question, answer),
        asyncio.to_thread(_run_critic_safely, "logic", evaluate_logic, question, answer),
        asyncio.to_thread(_run_critic_safely, "completeness", evaluate_completeness, question, answer),
    )

    critiques: dict[str, Critique | None] = {}
    warnings: list[str] = []

    for name, critique, error in results:
        if error is not None:
            warnings.append(f"{name} critic failed: {error}")
            critiques[name] = None
        else:
            critiques[name] = critique

    if all(c is None for c in critiques.values()):
        raise RuntimeError("All critics failed. Arbitration cannot be completed.")

    return adjudicate(
        accuracy=critiques["accuracy"],
        logic=critiques["logic"],
        completeness=critiques["completeness"],
        warnings=warnings,
    )
