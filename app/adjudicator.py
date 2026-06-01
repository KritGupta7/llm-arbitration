from app.models.critique import Critique


def adjudicate(
    accuracy: Critique,
    logic: Critique,
    completeness: Critique
):
    avg_score = (
        accuracy.score
        + logic.score
        + completeness.score
    ) / 3

    return {
        "final_score": round(avg_score, 2),
        "accuracy": accuracy,
        "logic": logic,
        "completeness": completeness
    }