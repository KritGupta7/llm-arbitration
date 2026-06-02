from app.models.critique import Critique, Issue
from app.disagreement_detector import detect_disagreements


def make_critique(
    dimension: str,
    score: int,
    confidence: float = 0.8,
    issues: list[Issue] | None = None,
) -> Critique:
    return Critique(
        dimension=dimension,
        score=score,
        confidence=confidence,
        issues=issues or [],
        explanation="test",
    )


def make_severe_issue() -> Issue:
    return Issue(quote="some quote", problem="serious problem", severity=4)


# ── A. No disagreement ────────────────────────────────────────────────────────

def test_no_disagreement_aligned_scores():
    accuracy = make_critique("accuracy", score=5)
    logic = make_critique("logic", score=5)
    completeness = make_critique("completeness", score=4)

    result = detect_disagreements(accuracy, logic, completeness)

    types = [d.type for d in result]
    assert "score_gap" not in types


# ── B. Score gap ──────────────────────────────────────────────────────────────

def test_score_gap_detected():
    accuracy = make_critique("accuracy", score=2)
    logic = make_critique("logic", score=5)
    completeness = make_critique("completeness", score=5)

    result = detect_disagreements(accuracy, logic, completeness)

    types = [d.type for d in result]
    assert "score_gap" in types


def test_score_gap_severity_medium_when_gap_is_two():
    accuracy = make_critique("accuracy", score=3)
    logic = make_critique("logic", score=5)
    completeness = make_critique("completeness", score=4)

    result = detect_disagreements(accuracy, logic, completeness)
    gap_disagreements = [d for d in result if d.type == "score_gap"]

    assert len(gap_disagreements) == 1
    assert gap_disagreements[0].severity == "medium"


def test_score_gap_severity_high_when_gap_is_three_or_more():
    accuracy = make_critique("accuracy", score=2)
    logic = make_critique("logic", score=5)
    completeness = make_critique("completeness", score=5)

    result = detect_disagreements(accuracy, logic, completeness)
    gap_disagreements = [d for d in result if d.type == "score_gap"]

    assert len(gap_disagreements) == 1
    assert gap_disagreements[0].severity == "high"


# ── C. Severe issue vs high score ─────────────────────────────────────────────

def test_severe_issue_vs_high_score_detected():
    accuracy = make_critique("accuracy", score=2, issues=[make_severe_issue()])
    logic = make_critique("logic", score=4)
    completeness = make_critique("completeness", score=4)

    result = detect_disagreements(accuracy, logic, completeness)

    types = [d.type for d in result]
    assert "severe_issue_vs_high_score" in types


def test_no_severe_issue_vs_high_score_when_all_issues_low():
    minor_issue = Issue(quote="q", problem="minor", severity=2)
    accuracy = make_critique("accuracy", score=3, issues=[minor_issue])
    logic = make_critique("logic", score=5)
    completeness = make_critique("completeness", score=5)

    result = detect_disagreements(accuracy, logic, completeness)

    types = [d.type for d in result]
    assert "severe_issue_vs_high_score" not in types


# ── D. Low score without issues ───────────────────────────────────────────────

def test_low_score_without_issues_detected():
    accuracy = make_critique("accuracy", score=2, issues=[])
    logic = make_critique("logic", score=4)
    completeness = make_critique("completeness", score=4)

    result = detect_disagreements(accuracy, logic, completeness)

    types = [d.type for d in result]
    assert "low_score_without_issues" in types


def test_no_low_score_without_issues_when_issues_present():
    accuracy = make_critique("accuracy", score=2, issues=[make_severe_issue()])
    logic = make_critique("logic", score=4)
    completeness = make_critique("completeness", score=4)

    result = detect_disagreements(accuracy, logic, completeness)

    types = [d.type for d in result]
    assert "low_score_without_issues" not in types


def test_no_disagreement_returns_empty_list():
    accuracy = make_critique("accuracy", score=5)
    logic = make_critique("logic", score=5)
    completeness = make_critique("completeness", score=5)

    result = detect_disagreements(accuracy, logic, completeness)
    assert result == []
