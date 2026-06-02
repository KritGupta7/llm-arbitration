import asyncio
from typing import Callable

from app.critics.accuracy import evaluate_accuracy
from app.critics.logic import evaluate_logic
from app.critics.completeness import evaluate_completeness
from app.adjudicator import _fallback_critique
from app.disagreement_detector import detect_disagreements
from app.adjudicators.llm_adjudicator import adjudicate_with_llm
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
    # Step 1: Run critics concurrently with graceful failure handling
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

    # Step 2: Apply fallbacks for any failed critics
    accuracy = critiques["accuracy"] or _fallback_critique("accuracy")
    logic = critiques["logic"] or _fallback_critique("logic")
    completeness = critiques["completeness"] or _fallback_critique("completeness")

    # Step 3: Detect disagreements across critic reports
    disagreements = detect_disagreements(accuracy, logic, completeness)

    # Step 4 & 5: LLM adjudicator produces the final verdict
    return adjudicate_with_llm(
        question=question,
        answer=answer,
        accuracy=accuracy,
        logic=logic,
        completeness=completeness,
        disagreements=disagreements,
        warnings=warnings,
    )
