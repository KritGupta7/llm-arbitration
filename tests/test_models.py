import pytest
from pydantic import ValidationError

from app.models.critique import Issue, Critique
from app.models.disagreement import Disagreement
from app.models.arbitration_result import ArbitrationResult


# ── Issue ─────────────────────────────────────────────────────────────────────

def make_issue(severity: int) -> Issue:
    return Issue(quote="some quote", problem="some problem", severity=severity)


def test_issue_severity_min_valid():
    issue = make_issue(1)
    assert issue.severity == 1


def test_issue_severity_max_valid():
    issue = make_issue(5)
    assert issue.severity == 5


def test_issue_severity_too_low():
    with pytest.raises(ValidationError):
        make_issue(0)


def test_issue_severity_too_high():
    with pytest.raises(ValidationError):
        make_issue(6)


# ── Critique ──────────────────────────────────────────────────────────────────

def make_critique(score: int = 3, confidence: float = 0.8) -> Critique:
    return Critique(
        dimension="accuracy",
        score=score,
        confidence=confidence,
        issues=[],
        explanation="test explanation",
    )


def test_critique_score_min_valid():
    c = make_critique(score=1)
    assert c.score == 1


def test_critique_score_max_valid():
    c = make_critique(score=5)
    assert c.score == 5


def test_critique_score_too_low():
    with pytest.raises(ValidationError):
        make_critique(score=0)


def test_critique_score_too_high():
    with pytest.raises(ValidationError):
        make_critique(score=6)


def test_critique_confidence_min_valid():
    c = make_critique(confidence=0.0)
    assert c.confidence == 0.0


def test_critique_confidence_max_valid():
    c = make_critique(confidence=1.0)
    assert c.confidence == 1.0


def test_critique_confidence_below_zero():
    with pytest.raises(ValidationError):
        make_critique(confidence=-0.1)


def test_critique_confidence_above_one():
    with pytest.raises(ValidationError):
        make_critique(confidence=1.1)


# ── ArbitrationResult ─────────────────────────────────────────────────────────

def _base_critique(dimension: str) -> Critique:
    return Critique(
        dimension=dimension,
        score=4,
        confidence=0.9,
        issues=[],
        explanation="fine",
    )


def test_arbitration_result_valid():
    result = ArbitrationResult(
        final_score=4.0,
        confidence_level="high",
        summary="looks good",
        confirmed_issues=[],
        accuracy=_base_critique("accuracy"),
        logic=_base_critique("logic"),
        completeness=_base_critique("completeness"),
    )
    assert result.final_score == 4.0
    assert result.confidence_level == "high"


def test_arbitration_result_with_confirmed_issues():
    issue = Issue(quote="q", problem="p", severity=4)
    result = ArbitrationResult(
        final_score=2.0,
        confidence_level="high",
        summary="bad answer",
        confirmed_issues=[issue],
        accuracy=_base_critique("accuracy"),
        logic=_base_critique("logic"),
        completeness=_base_critique("completeness"),
    )
    assert len(result.confirmed_issues) == 1
    assert result.confirmed_issues[0].severity == 4


def test_arbitration_result_dismissed_issues_default_empty():
    result = ArbitrationResult(
        final_score=4.0,
        confidence_level="high",
        summary="ok",
        confirmed_issues=[],
        accuracy=_base_critique("accuracy"),
        logic=_base_critique("logic"),
        completeness=_base_critique("completeness"),
    )
    assert result.dismissed_issues == []


def test_arbitration_result_supports_disagreements_and_warnings():
    disagreement = Disagreement(
        type="score_gap",
        description="gap between critics",
        severity="high",
    )
    result = ArbitrationResult(
        final_score=3.0,
        confidence_level="medium",
        summary="mixed",
        confirmed_issues=[],
        disagreements=[disagreement],
        warnings=["logic critic failed: timeout"],
        accuracy=_base_critique("accuracy"),
        logic=_base_critique("logic"),
        completeness=_base_critique("completeness"),
    )
    assert len(result.disagreements) == 1
    assert len(result.warnings) == 1
