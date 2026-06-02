from app.models.critique import Critique
from app.models.disagreement import Disagreement


def detect_disagreements(
    accuracy: Critique,
    logic: Critique,
    completeness: Critique,
) -> list[Disagreement]:
    critics = [accuracy, logic, completeness]
    disagreements: list[Disagreement] = []

    # Rule 1: Score gap
    scores = [c.score for c in critics]
    gap = max(scores) - min(scores)
    if gap >= 2:
        high_critic = max(critics, key=lambda c: c.score)
        low_critic = min(critics, key=lambda c: c.score)
        severity = "high" if gap >= 3 else "medium"
        disagreements.append(Disagreement(
            type="score_gap",
            description=(
                f"Score gap of {gap} between critics: "
                f"{low_critic.dimension} scored {low_critic.score} "
                f"while {high_critic.dimension} scored {high_critic.score}."
            ),
            severity=severity,
        ))

    # Rule 2: Severe issue in one critic vs high score in another
    critics_with_severe_issues = [
        c for c in critics if any(issue.severity >= 4 for issue in c.issues)
    ]
    high_scoring_critics = [c for c in critics if c.score >= 4]

    if critics_with_severe_issues and high_scoring_critics:
        severe_names = ", ".join(c.dimension for c in critics_with_severe_issues)
        high_names = ", ".join(c.dimension for c in high_scoring_critics)
        disagreements.append(Disagreement(
            type="severe_issue_vs_high_score",
            description=(
                f"{severe_names} found at least one severe issue (severity >= 4) "
                f"while {high_names} scored the answer highly (score >= 4). "
                "Critics may be evaluating different aspects with conflicting conclusions."
            ),
            severity="high",
        ))

    # Rule 3: Low score without any issues
    for critic in critics:
        if critic.score <= 2 and not critic.issues:
            disagreements.append(Disagreement(
                type="low_score_without_issues",
                description=(
                    f"{critic.dimension} critic gave a low score of {critic.score} "
                    "but reported no concrete issues to support it."
                ),
                severity="medium",
            ))

    return disagreements
