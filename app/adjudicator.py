from app.models.critique import Critique
from app.models.arbitration_result import ArbitrationResult


def _fallback_critique(dimension: str) -> Critique:
    return Critique(
        dimension=dimension,
        score=1,
        confidence=0.0,
        issues=[],
        explanation="This critic failed and could not evaluate the answer.",
    )


def adjudicate(
    accuracy: Critique | None,
    logic: Critique | None,
    completeness: Critique | None,
    warnings: list[str] | None = None,
) -> ArbitrationResult:
    accuracy = accuracy or _fallback_critique("accuracy")
    logic = logic or _fallback_critique("logic")
    completeness = completeness or _fallback_critique("completeness")

    final_score = round(
        (accuracy.score + logic.score + completeness.score) / 3, 2
    )

    avg_confidence = (
        accuracy.confidence + logic.confidence + completeness.confidence
    ) / 3

    if avg_confidence >= 0.8:
        confidence_level = "high"
    elif avg_confidence >= 0.5:
        confidence_level = "medium"
    else:
        confidence_level = "low"

    if final_score >= 4:
        summary = "The answer is generally strong with minor or no issues."
    elif final_score >= 3:
        summary = "The answer is partially acceptable but has important issues."
    else:
        summary = "The answer has serious quality issues and should be reviewed."

    all_issues = accuracy.issues + logic.issues + completeness.issues
    confirmed_issues = [issue for issue in all_issues if issue.severity >= 4]

    return ArbitrationResult(
        final_score=final_score,
        confidence_level=confidence_level,
        summary=summary,
        confirmed_issues=confirmed_issues,
        warnings=warnings or [],
        accuracy=accuracy,
        logic=logic,
        completeness=completeness,
    )
