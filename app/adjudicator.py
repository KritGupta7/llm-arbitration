from app.models.critique import Critique
from app.models.arbitration_result import ArbitrationResult


def adjudicate(
    accuracy: Critique,
    logic: Critique,
    completeness: Critique
) -> ArbitrationResult:
    avg_score = (
        accuracy.score
        + logic.score
        + completeness.score
    ) / 3

    return ArbitrationResult(
        final_score=round(avg_score, 2),
        accuracy=accuracy,
        logic=logic,
        completeness=completeness
    )