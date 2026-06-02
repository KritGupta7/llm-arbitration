# Architecture: LLM Output Arbitration System

This document explains the architecture and design decisions behind the LLM Output Arbitration System.

---

## 1. Purpose

The system evaluates LLM-generated answers using a multi-agent arbitration pipeline.

Instead of trusting one evaluator, it uses multiple specialized critics and an adjudicator to produce a more reliable final verdict.

The system is designed to answer:

```
Is this LLM-generated answer accurate, logical, complete, and trustworthy?
```

---

## 2. High-Level Architecture

```
┌─────────────────────────────┐
│        User Input           │
│   Question + LLM Answer     │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│    API / Dashboard / CLI    │
│  FastAPI / Streamlit / CLI  │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  Arbitration Orchestrator   │
│     app/arbitration.py      │
└──────┬──────────┬───────────┘
       │          │          │
       ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌───────────────────┐
│ Accuracy │ │  Logic   │ │  Completeness      │
│  Critic  │ │  Critic  │ │  Critic            │
│app/critics│ │app/critics│ │app/critics/...    │
└──────────┘ └──────────┘ └───────────────────┘
       │          │                │
       └──────────┴────────────────┘
                  │
                  ▼
┌─────────────────────────────┐
│    Graceful Failure         │
│       Handler               │
│  (fallback Critiques for    │
│    failed critics)          │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   Disagreement Detector     │
│ app/disagreement_detector.py│
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│      LLM Adjudicator        │
│ app/adjudicators/           │
│   llm_adjudicator.py        │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   Final ArbitrationResult   │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│      SQLite Storage         │
│      arbitrations.db        │
└────────────┬────────────────┘
             │
     ┌───────┴────────┐
     ▼                ▼
 History           Analytics
 /arbitrations     /analytics
```

---

## 3. Component Breakdown

### 3.1 Entry Points

The system exposes three entry points that all feed into the same arbitration pipeline:

| Entry Point | File | Description |
|---|---|---|
| FastAPI API | `app/api.py` | HTTP endpoints for single arbitration, batch, history, analytics |
| Streamlit Dashboard | `streamlit_app.py` | Visual frontend that calls the FastAPI backend |
| CLI | `main.py` | Interactive terminal mode for quick testing |

### 3.2 Arbitration Orchestrator

**File:** `app/arbitration.py`

Responsible for coordinating the full pipeline:

1. Launches all three critics concurrently using `asyncio.to_thread` + `asyncio.gather`
2. Applies graceful failure handling — wraps each critic call in a safe wrapper
3. Produces fallback `Critique` objects for any critics that fail
4. Calls the disagreement detector
5. Calls the LLM adjudicator
6. Returns the final `ArbitrationResult`

**Design decision:** Critics run concurrently to reduce total latency. Each makes an independent OpenAI API call, so parallel execution cuts wall time roughly by 3×.

### 3.3 Critics

**Directory:** `app/critics/`

Each critic is a standalone function that calls the OpenAI API, asks it to return structured JSON, parses the response, and returns a `Critique` Pydantic model.

| Critic | File | Evaluates |
|---|---|---|
| Accuracy | `accuracy.py` | Whether stated facts are verifiably correct |
| Logic | `logic.py` | Whether reasoning is coherent and non-contradictory |
| Completeness | `completeness.py` | Whether the answer adequately addresses the question |

Each critic returns:

```json
{
  "dimension": "accuracy",
  "score": 2,
  "confidence": 0.85,
  "issues": [
    {
      "quote": "exact verbatim phrase",
      "problem": "why it is wrong",
      "severity": 4
    }
  ],
  "explanation": "overall evaluation"
}
```

**Design decision:** Critics are calibrated to evaluate relative to the scope of the original question. A concise correct answer to a simple question should score 4–5. Severity 4–5 is reserved for factual errors, contradictions, and harmful claims — not missing optional detail.

### 3.4 Graceful Failure Handler

**File:** `app/arbitration.py` (`_run_critic_safely`)

Each critic is wrapped with a safe execution function that catches all exceptions. Failed critics return `(name, None, error_message)` instead of crashing the pipeline.

If all three critics fail, a `RuntimeError` is raised and arbitration is aborted. If one or two fail, fallback `Critique` objects are generated with `score=1`, `confidence=0.0`, and a descriptive explanation.

Failures are captured as `warnings` in the final `ArbitrationResult`.

### 3.5 Disagreement Detector

**File:** `app/disagreement_detector.py`

Three rule-based checks run after the critics complete:

| Rule | Trigger | Severity |
|---|---|---|
| `score_gap` | Max critic score − min critic score ≥ 2 | `"medium"` if gap=2, `"high"` if gap≥3 |
| `severe_issue_vs_high_score` | One critic has a severity ≥ 4 issue while another scores ≥ 4 | `"high"` |
| `low_score_without_issues` | A critic scores ≤ 2 but reports no issues | `"medium"` |

Returns `list[Disagreement]`, which is passed to the LLM adjudicator as context.

### 3.6 LLM Adjudicator

**File:** `app/adjudicators/llm_adjudicator.py`

The adjudicator receives:
- Original question and answer
- All three critic reports (serialized as JSON)
- Detected disagreements
- Warnings from failed critics

It calls the OpenAI API once and asks it to act as a senior quality judge. The LLM is instructed to:

- Evaluate issues relative to what the question actually asked for
- Confirm genuine issues and dismiss overly strict ones
- Resolve score gap disagreements by re-reading the original question
- Produce an independent `final_score`, not a blind average

Returns: `final_score`, `confidence_level`, `summary`, `confirmed_issues`, `dismissed_issues`, `disagreements`

The Python function then attaches the original critic reports and warnings to build the complete `ArbitrationResult`.

**Design decision:** The adjudicator is LLM-based rather than rule-based because resolving critic disagreements requires contextual judgment. A rule-based adjudicator that simply averages scores would produce misleading results when one critic is clearly more relevant to the question than the others.

### 3.7 Data Models

**Directory:** `app/models/`

| Model | File | Purpose |
|---|---|---|
| `ArbitrationRequest` | `arbitration_request.py` | Input: `question`, `answer` |
| `Issue` | `critique.py` | Individual issue: `quote`, `problem`, `severity` |
| `Critique` | `critique.py` | Critic report with Pydantic field validation |
| `Disagreement` | `disagreement.py` | Inter-critic disagreement |
| `ArbitrationResult` | `arbitration_result.py` | Full final result |
| `ArbitrationRecord` | `db_models.py` | SQLAlchemy ORM model for SQLite |

**Design decision:** `Critique.score` is validated as `int` with `Field(ge=1, le=5)` and `Critique.confidence` as `float` with `Field(ge=0.0, le=1.0)`. This catches out-of-range LLM responses at parse time.

### 3.8 Storage Layer

**Files:** `app/database.py`, `app/models/db_models.py`, `app/repositories/arbitration_repository.py`

SQLite is used for local storage via SQLAlchemy 2.0. The full `ArbitrationResult` is stored as serialized JSON in `result_json`. Key numeric fields (`final_score`, `confidence_level`) are also stored as separate columns for efficient querying without JSON parsing.

Repository functions:

| Function | Description |
|---|---|
| `save_arbitration` | Saves a result after every arbitration |
| `get_arbitration` | Retrieves a single record by ID |
| `list_arbitrations` | Returns recent records (default limit: 20) |
| `list_all_arbitrations` | Returns all records (used by analytics) |

### 3.9 Analytics Service

**File:** `app/services/analytics_service.py`

Reads all stored records, parses each `result_json`, and computes aggregate metrics:

- Total arbitrations
- Average final score
- Confidence level distribution
- Quality bucket distribution (`high` / `medium` / `low`)
- Average per-critic scores
- Total confirmed and dismissed issues
- Most common confirmed issue severity
- Total disagreements and warnings

Malformed records are skipped and counted in `invalid_record_count` rather than crashing the endpoint.

---

## 4. API Design

**File:** `app/api.py`

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Health check |
| `/arbitrate` | `POST` | Run single arbitration, save to DB, return `id` + result |
| `/arbitrate/batch` | `POST` | Run up to 10 arbitrations, per-item error handling |
| `/arbitrations` | `GET` | List recent records (lightweight, no full JSON) |
| `/arbitrations/{id}` | `GET` | Return full stored result for a given ID |
| `/analytics` | `GET` | Aggregate statistics |

**Design decision:** `GET /arbitrations` returns only summary fields (`id`, `question`, `answer`, `final_score`, `confidence_level`, `created_at`) to keep list responses fast. The full JSON is only deserialized when a specific record is requested via `GET /arbitrations/{id}`.

**Database initialization:** Tables are created on startup using FastAPI's `lifespan` context manager with `Base.metadata.create_all(bind=engine)`.

---

## 5. Concurrency Model

```
async arbitrate()
    │
    ├── asyncio.to_thread(_run_critic_safely, "accuracy", ...)
    ├── asyncio.to_thread(_run_critic_safely, "logic", ...)
    └── asyncio.to_thread(_run_critic_safely, "completeness", ...)
              │
          asyncio.gather (all three run in parallel)
              │
    detect_disagreements()       ← synchronous, fast
              │
    adjudicate_with_llm()        ← one OpenAI call
              │
    save_arbitration()           ← synchronous SQLite write
```

Critics run in thread pool workers (via `asyncio.to_thread`) because the OpenAI Python client is synchronous. The disagreement detector and DB write are synchronous but fast. The LLM adjudicator makes one final OpenAI call.

**Batch arbitration** processes items sequentially. Each item's three critics still run concurrently internally.

---

## 6. Error Handling Strategy

| Layer | Failure | Behavior |
|---|---|---|
| Critic | `json.JSONDecodeError` | Raises `ValueError` with critic name + raw content |
| Critic | Any exception | Caught by `_run_critic_safely`; adds warning, generates fallback |
| All critics | All three fail | Raises `RuntimeError`; arbitration aborted |
| LLM Adjudicator | `json.JSONDecodeError` | Raises `ValueError` with raw content |
| Analytics | Malformed `result_json` | Skips record; increments `invalid_record_count` |
| Batch endpoint | Individual item fails | Item returns `"success": false`; batch continues |
| Streamlit | Backend not running | Shows user-friendly error; no stack trace |

---

## 7. Design Decisions Summary

| Decision | Rationale |
|---|---|
| Three independent critics | Single-evaluator LLMs can miss issues that specialized critics catch |
| Concurrent critic execution | Reduces latency by ~3× compared to sequential calls |
| Rule-based disagreement detection | Fast, deterministic, and explainable without an extra LLM call |
| LLM-based adjudicator | Resolving disagreements requires contextual judgment that rules cannot capture |
| Question-scoped calibration | Prevents over-penalizing concise correct answers for missing optional detail |
| Fallback critiques for failed critics | Allows partial results instead of complete failure |
| JSON storage for full result | Avoids over-normalizing a schema that may evolve; fast for reads |
| SQLite for storage | Simple, zero-config, sufficient for local development and portfolio demos |
| Streamlit calls FastAPI | Keeps the backend the single source of truth; no duplicated logic |
