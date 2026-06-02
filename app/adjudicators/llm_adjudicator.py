import json
from app.services.openai_client import client
from app.models.critique import Critique, Issue
from app.models.disagreement import Disagreement
from app.models.arbitration_result import ArbitrationResult


def adjudicate_with_llm(
    question: str,
    answer: str,
    accuracy: Critique,
    logic: Critique,
    completeness: Critique,
    disagreements: list[Disagreement],
    warnings: list[str],
) -> ArbitrationResult:
    critic_reports = {
        "accuracy": accuracy.model_dump(),
        "logic": logic.model_dump(),
        "completeness": completeness.model_dump(),
    }
    disagreements_data = [d.model_dump() for d in disagreements]

    prompt = f"""You are a senior AI output quality judge. Three specialist critics have already evaluated an LLM answer. Your job is to review their findings, resolve any disagreements, and deliver a final authoritative verdict.

---
ORIGINAL QUESTION:
{question}

ORIGINAL ANSWER:
{answer}

---
CRITIC REPORTS:
{json.dumps(critic_reports, indent=2)}

---
DETECTED DISAGREEMENTS:
{json.dumps(disagreements_data, indent=2)}

---
WARNINGS (critics that failed):
{json.dumps(warnings, indent=2)}

---
YOUR TASK:
You are the final judge. Your primary responsibility is to evaluate the answer relative to what the original question actually asked for.

Before accepting any critic issue, ask yourself: "Did the original question require this information?"
- If YES and the answer omits or gets it wrong: the issue is confirmed.
- If NO (it is optional detail, advanced context, or helpful but not required): dismiss the issue or assign it severity 1-2 at most.

Adjudication principles:
1. A concise, accurate answer to a simple question should score 4.0 to 5.0. Do not let critics drag a good answer below 4.0 over missing optional details.
2. Severity 4-5 is reserved for: factual errors, contradictions, harmful/misleading claims, or a failure to answer the core question.
3. If a critic flags missing "advanced detail" or "background context" that the question did not ask for, put that issue in dismissed_issues.
4. Resolve score_gap disagreements by re-reading the original question and deciding which critic was calibrated correctly. Do not simply average.
5. Your final_score reflects your independent judgment, not the average of critic scores.

Return ONLY valid JSON. No markdown, no code fences, no extra text. The JSON must match this exact structure:

{{
  "final_score": 3.0,
  "confidence_level": "high",
  "summary": "A short paragraph explaining the overall quality of the answer.",
  "confirmed_issues": [
    {{
      "quote": "exact verbatim phrase from the answer",
      "problem": "why this is a genuine problem required by the question",
      "severity": 4
    }}
  ],
  "dismissed_issues": [
    {{
      "quote": "exact verbatim phrase from the answer",
      "problem": "why this was raised by a critic but is optional detail or not required by the question",
      "severity": 2
    }}
  ],
  "disagreements": [
    {{
      "type": "score_gap",
      "description": "brief description of the disagreement and how you resolved it",
      "severity": "high"
    }}
  ]
}}

Rules:
- final_score: float from 1.0 to 5.0 reflecting your holistic judgment relative to the question scope
- confidence_level: exactly one of "low", "medium", "high"
- confirmed_issues: only issues that are genuinely required by the question and represent real errors or gaps; empty list [] if none
- dismissed_issues: issues raised by critics that are optional, overly strict, or not required by the question; empty list [] if none
- disagreements: only carry forward disagreements that remain unresolved or are noteworthy; empty list [] if critics were well-aligned
- severity in issues: integer 1 (minor) to 5 (critical)
- severity in disagreements: exactly one of "low", "medium", "high"
- Do not regenerate the critic reports — only return the fields above
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content.strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM adjudicator returned invalid JSON: {exc}\nRaw content: {content}"
        ) from exc

    confirmed_issues = [Issue(**i) for i in data.get("confirmed_issues", [])]
    dismissed_issues = [Issue(**i) for i in data.get("dismissed_issues", [])]
    resolved_disagreements = [
        Disagreement(**d) for d in data.get("disagreements", [])
    ]

    return ArbitrationResult(
        final_score=float(data["final_score"]),
        confidence_level=data["confidence_level"],
        summary=data["summary"],
        confirmed_issues=confirmed_issues,
        dismissed_issues=dismissed_issues,
        disagreements=resolved_disagreements,
        warnings=warnings,
        accuracy=accuracy,
        logic=logic,
        completeness=completeness,
    )
