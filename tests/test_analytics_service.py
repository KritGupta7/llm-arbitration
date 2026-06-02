import json
from dataclasses import dataclass

from app.services.analytics_service import calculate_analytics_from_records


@dataclass
class FakeRecord:
    final_score: float
    confidence_level: str
    result_json: str


def _make_result_json(
    accuracy_score: int = 4,
    logic_score: int = 4,
    completeness_score: int = 4,
    confirmed_issues: list | None = None,
    dismissed_issues: list | None = None,
    disagreements: list | None = None,
    warnings: list | None = None,
) -> str:
    return json.dumps({
        "accuracy": {"score": accuracy_score},
        "logic": {"score": logic_score},
        "completeness": {"score": completeness_score},
        "confirmed_issues": confirmed_issues or [],
        "dismissed_issues": dismissed_issues or [],
        "disagreements": disagreements or [],
        "warnings": warnings or [],
    })


# ── A. Empty records ──────────────────────────────────────────────────────────

def test_empty_records_returns_zeros():
    result = calculate_analytics_from_records([])

    assert result["total_arbitrations"] == 0
    assert result["average_final_score"] == 0
    assert result["confidence_counts"] == {"high": 0, "medium": 0, "low": 0}
    assert result["quality_counts"] == {
        "high_quality": 0, "medium_quality": 0, "low_quality": 0
    }
    assert result["average_critic_scores"] == {"accuracy": 0, "logic": 0, "completeness": 0}
    assert result["total_confirmed_issues"] == 0
    assert result["total_dismissed_issues"] == 0
    assert result["most_common_confirmed_issue_severity"] is None
    assert result["disagreement_count"] == 0
    assert result["warning_count"] == 0


# ── B. Single record ──────────────────────────────────────────────────────────

def test_single_high_quality_record():
    record = FakeRecord(
        final_score=4.5,
        confidence_level="high",
        result_json=_make_result_json(
            accuracy_score=5,
            logic_score=4,
            completeness_score=5,
        ),
    )
    result = calculate_analytics_from_records([record])

    assert result["total_arbitrations"] == 1
    assert result["average_final_score"] == 4.5
    assert result["confidence_counts"] == {"high": 1, "medium": 0, "low": 0}
    assert result["quality_counts"] == {
        "high_quality": 1, "medium_quality": 0, "low_quality": 0
    }
    assert result["average_critic_scores"]["accuracy"] == 5.0
    assert result["average_critic_scores"]["logic"] == 4.0
    assert result["average_critic_scores"]["completeness"] == 5.0


def test_single_low_quality_record_with_issues():
    confirmed = [{"quote": "wrong claim", "problem": "factual error", "severity": 5}]
    dismissed = [{"quote": "minor", "problem": "not required", "severity": 1}]
    record = FakeRecord(
        final_score=2.0,
        confidence_level="high",
        result_json=_make_result_json(
            accuracy_score=1,
            logic_score=3,
            completeness_score=3,
            confirmed_issues=confirmed,
            dismissed_issues=dismissed,
        ),
    )
    result = calculate_analytics_from_records([record])

    assert result["total_confirmed_issues"] == 1
    assert result["total_dismissed_issues"] == 1
    assert result["most_common_confirmed_issue_severity"] == 5
    assert result["quality_counts"]["low_quality"] == 1


# ── C. Two records ────────────────────────────────────────────────────────────

def test_two_records_average_score():
    r1 = FakeRecord(
        final_score=2.0,
        confidence_level="high",
        result_json=_make_result_json(accuracy_score=2, logic_score=2, completeness_score=2),
    )
    r2 = FakeRecord(
        final_score=4.0,
        confidence_level="medium",
        result_json=_make_result_json(accuracy_score=4, logic_score=4, completeness_score=4),
    )
    result = calculate_analytics_from_records([r1, r2])

    assert result["total_arbitrations"] == 2
    assert result["average_final_score"] == 3.0
    assert result["confidence_counts"] == {"high": 1, "medium": 1, "low": 0}
    assert result["quality_counts"]["high_quality"] == 1
    assert result["quality_counts"]["low_quality"] == 1
    assert result["average_critic_scores"]["accuracy"] == 3.0


def test_disagreements_and_warnings_counted():
    record = FakeRecord(
        final_score=3.0,
        confidence_level="medium",
        result_json=_make_result_json(
            disagreements=[{"type": "score_gap", "description": "gap", "severity": "high"}],
            warnings=["logic critic failed: timeout"],
        ),
    )
    result = calculate_analytics_from_records([record])

    assert result["disagreement_count"] == 1
    assert result["warning_count"] == 1


def test_most_common_severity_correct():
    confirmed = [
        {"quote": "a", "problem": "p", "severity": 4},
        {"quote": "b", "problem": "q", "severity": 4},
        {"quote": "c", "problem": "r", "severity": 5},
    ]
    record = FakeRecord(
        final_score=2.0,
        confidence_level="low",
        result_json=_make_result_json(confirmed_issues=confirmed),
    )
    result = calculate_analytics_from_records([record])

    assert result["most_common_confirmed_issue_severity"] == 4


def test_malformed_result_json_skipped():
    good = FakeRecord(
        final_score=4.0,
        confidence_level="high",
        result_json=_make_result_json(),
    )
    bad = FakeRecord(
        final_score=3.0,
        confidence_level="medium",
        result_json="NOT VALID JSON {{{",
    )
    result = calculate_analytics_from_records([good, bad])

    assert result["total_arbitrations"] == 1
    assert result["invalid_record_count"] == 1
