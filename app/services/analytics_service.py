import json
from collections import Counter
from typing import Protocol

from app.repositories.arbitration_repository import list_all_arbitrations

_EMPTY = {
    "total_arbitrations": 0,
    "average_final_score": 0,
    "confidence_counts": {"high": 0, "medium": 0, "low": 0},
    "quality_counts": {"high_quality": 0, "medium_quality": 0, "low_quality": 0},
    "average_critic_scores": {"accuracy": 0, "logic": 0, "completeness": 0},
    "total_confirmed_issues": 0,
    "total_dismissed_issues": 0,
    "most_common_confirmed_issue_severity": None,
    "disagreement_count": 0,
    "warning_count": 0,
    "invalid_record_count": 0,
}


class _RecordLike(Protocol):
    final_score: float
    confidence_level: str
    result_json: str


def calculate_analytics_from_records(records: list[_RecordLike]) -> dict:
    """
    Pure calculation function. Accepts any list of record-like objects that
    expose final_score, confidence_level, and result_json. Has no database
    dependency, making it straightforward to unit test.
    """
    if not records:
        return dict(_EMPTY)

    confidence_counts = {"high": 0, "medium": 0, "low": 0}
    quality_counts = {"high_quality": 0, "medium_quality": 0, "low_quality": 0}
    critic_score_totals = {"accuracy": 0.0, "logic": 0.0, "completeness": 0.0}

    total_confirmed_issues = 0
    total_dismissed_issues = 0
    confirmed_severities: list[int] = []
    disagreement_count = 0
    warning_count = 0
    invalid_record_count = 0
    valid_count = 0
    score_sum = 0.0

    for record in records:
        try:
            data = json.loads(record.result_json)
        except (json.JSONDecodeError, TypeError):
            invalid_record_count += 1
            continue

        valid_count += 1
        score_sum += record.final_score

        level = record.confidence_level
        if level in confidence_counts:
            confidence_counts[level] += 1

        if record.final_score >= 4:
            quality_counts["high_quality"] += 1
        elif record.final_score >= 3:
            quality_counts["medium_quality"] += 1
        else:
            quality_counts["low_quality"] += 1

        for dim in ("accuracy", "logic", "completeness"):
            critic_block = data.get(dim, {})
            critic_score_totals[dim] += critic_block.get("score", 0)

        confirmed = data.get("confirmed_issues", [])
        total_confirmed_issues += len(confirmed)
        for issue in confirmed:
            sev = issue.get("severity")
            if isinstance(sev, int):
                confirmed_severities.append(sev)

        total_dismissed_issues += len(data.get("dismissed_issues", []))
        disagreement_count += len(data.get("disagreements", []))
        warning_count += len(data.get("warnings", []))

    if valid_count == 0:
        result = dict(_EMPTY)
        result["invalid_record_count"] = invalid_record_count
        return result

    average_final_score = round(score_sum / valid_count, 2)
    average_critic_scores = {
        dim: round(total / valid_count, 2)
        for dim, total in critic_score_totals.items()
    }

    most_common_severity = None
    if confirmed_severities:
        most_common_severity = Counter(confirmed_severities).most_common(1)[0][0]

    return {
        "total_arbitrations": valid_count,
        "average_final_score": average_final_score,
        "confidence_counts": confidence_counts,
        "quality_counts": quality_counts,
        "average_critic_scores": average_critic_scores,
        "total_confirmed_issues": total_confirmed_issues,
        "total_dismissed_issues": total_dismissed_issues,
        "most_common_confirmed_issue_severity": most_common_severity,
        "disagreement_count": disagreement_count,
        "warning_count": warning_count,
        "invalid_record_count": invalid_record_count,
    }


def get_analytics() -> dict:
    records = list_all_arbitrations()
    return calculate_analytics_from_records(records)
