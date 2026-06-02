LLM Output Arbitration System

A multi-agent evaluation system that reviews LLM-generated answers using multiple critic agents, disagreement detection, and an LLM adjudicator.

This project evaluates whether an AI-generated answer is accurate, logical, complete, and trustworthy. Instead of relying on a single evaluator, the system uses multiple specialized critics and then arbitrates between their opinions to produce a final verdict.

Why This Project Exists

Large language models can generate fluent answers that sound correct but may contain factual errors, incomplete explanations, or weak reasoning.

This project addresses that problem by building an arbitration pipeline:

1. A user provides a question and an LLM-generated answer.
2. Multiple critic agents evaluate the answer from different perspectives.
3. The system detects disagreements between critics.
4. An LLM adjudicator reviews the critic reports.
5. The final result is stored, analyzed, and displayed through an API and dashboard.

The goal is to simulate a more reliable evaluation workflow for AI-generated content.

Key Features

•	Multi-critic LLM evaluation
•	Accuracy critic
•	Logic critic
•	Completeness critic
•	Concurrent critic execution
•	Graceful critic failure handling
•	Disagreement detection
•	LLM-based adjudicator
•	Structured Pydantic response models
•	FastAPI backend
•	SQLite arbitration history storage
•	Analytics endpoint
•	Batch arbitration endpoint
•	Streamlit dashboard
•	CLI testing support

Tech Stack

•	Python 3.11+
•	FastAPI
•	Streamlit
•	OpenAI API
•	Pydantic
•	SQLAlchemy
•	SQLite
•	Uvicorn
•	Python-dotenv

System Overview

User Question + LLM Answer
        ↓
FastAPI / Streamlit / CLI
        ↓
Arbitration Orchestrator
        ↓
Accuracy Critic | Logic Critic | Completeness Critic
        ↓
Graceful Failure Handler
        ↓
Disagreement Detector
        ↓
LLM Adjudicator
        ↓
Final Arbitration Result
        ↓
SQLite Storage
        ↓
History, Analytics, Dashboard


Project Structure

llm-arbitration/
├── app/
│   ├── adjudicators/
│   │   └── llm_adjudicator.py
│   ├── critics/
│   │   ├── accuracy.py
│   │   ├── logic.py
│   │   └── completeness.py
│   ├── models/
│   │   ├── arbitration_request.py
│   │   ├── arbitration_result.py
│   │   ├── critique.py
│   │   └── db_models.py
│   ├── repositories/
│   │   └── arbitration_repository.py
│   ├── services/
│   │   ├── analytics_service.py
│   │   └── openai_client.py
│   ├── api.py
│   ├── arbitration.py
│   ├── database.py
│   └── disagreement_detector.py
├── main.py
├── streamlit_app.py
├── requirements.txt
├── .gitignore
└── README.md


How It Works

1. Input

The user provides:

{
  "question": "What causes tides?",
  "answer": "Tides are mainly caused by the sun."
}


2. Critic Agents

The system sends the answer to three critic agents.

Accuracy Critic checks whether the answer is factually correct.

Logic Critic checks whether the reasoning is coherent and non-contradictory.

Completeness Critic checks whether the answer sufficiently addresses the original question.

Each critic returns a structured report:

{
  "dimension": "accuracy",
  "score": 2,
  "confidence": 0.85,
  "issues": [
    {
      "quote": "Tides are mainly caused by the sun.",
      "problem": "The Moon is the primary driver of tides.",
      "severity": 4
    }
  ],
  "explanation": "The answer misidentifies the main cause of tides."
}


3. Disagreement Detection

The system checks whether critics disagree.

{
  "type": "score_gap",
  "description": "Accuracy scored much lower than logic and completeness.",
  "severity": "high"
}


4. LLM Adjudicator

The LLM adjudicator receives the original question, original answer, critic reports, detected disagreements, and warnings from failed critics. It then produces the final arbitration verdict.

5. Final Result

{
  "final_score": 2,
  "confidence_level": "high",
  "summary": "The answer partially addresses the question but incorrectly identifies the Sun as the main cause of tides.",
  "confirmed_issues": [
    {
      "quote": "Tides are mainly caused by the sun.",
      "problem": "The Moon is the primary driver of tides, while the Sun also contributes.",
      "severity": 4
    }
  ],
  "dismissed_issues": [],
  "disagreements": [],
  "warnings": [],
  "accuracy": {},
  "logic": {},
  "completeness": {}
}


API Endpoints

Health Check

GET /


Single Arbitration

POST /arbitrate


Request:

{
  "question": "What causes tides?",
  "answer": "Tides are mainly caused by the sun."
}


Response:

{
  "id": 1,
  "result": {
    "final_score": 2,
    "confidence_level": "high",
    "summary": "...",
    "confirmed_issues": [],
    "dismissed_issues": [],
    "disagreements": [],
    "warnings": [],
    "accuracy": {},
    "logic": {},
    "completeness": {}
  }
}


Batch Arbitration

POST /arbitrate/batch


Request:

[
  {
    "question": "What causes tides?",
    "answer": "Tides are mainly caused by the sun."
  },
  {
    "question": "What causes tides?",
    "answer": "Tides are caused mainly by the gravitational pull of the Moon, with the Sun also contributing."
  }
]


Batch size is limited to 10 items.

Arbitration History

GET /arbitrations


Returns recent saved arbitration records.

Single Stored Arbitration

GET /arbitrations/{id}


Returns a full saved arbitration result.

Analytics

GET /analytics


Returns aggregate evaluation statistics.

Setup Instructions

1. Clone the Repository

git clone git@github.com:KritGupta7/llm-arbitration.git
cd llm-arbitration


2. Create Virtual Environment

python -m venv venv
source venv/bin/activate


3. Install Dependencies

pip install -r requirements.txt


4. Create .env

Create a `.env` file in the project root:

OPENAI_API_KEY=your_api_key_here


Do not commit this file.

5. Run the FastAPI Backend

python -m uvicorn app.api:app --reload


Open:

http://127.0.0.1:8000/docs


6. Run the Streamlit Dashboard

In a second terminal:

streamlit run streamlit_app.py


7. Run CLI Mode

python main.py


Dashboard

The Streamlit dashboard provides three main sections:

Arbitrate

Submit a question and answer, then view final score, confidence level, summary, critic scores, confirmed issues, dismissed issues, disagreements, and warnings.

History

View recent arbitration records and load full results.

Analytics

View aggregate evaluation trends, including average scores, issue counts, confidence counts, and disagreement counts.

Example Test Cases

Bad Answer

Question:

What causes tides?


Answer:

Tides are mainly caused by the sun.


Expected result:

•	Low final score
•	Confirmed factual issue
•	Accuracy critic flags the answer
•	Stored in history

Good Answer

Question:

What causes tides?


Answer:

Tides are caused mainly by the gravitational pull of the Moon, with the Sun also contributing. The Moon's gravity pulls ocean water, creating bulges that we experience as high tides.


Expected result:

•	High final score
•	No major confirmed issues
•	Strong accuracy and logic scores
•	Stored in history

Data Storage

The project uses SQLite for local storage. Stored fields include id, question, answer, result_json, final_score, confidence_level, and created_at. The full arbitration result is stored as JSON.

The database file is ignored by git:

arbitrations.db
*.db


Security Notes

The project uses an OpenAI API key stored in `.env`.

The following files should never be committed:

.env
arbitrations.db
*.db


Current Limitations

•	The system depends on LLM-generated judgments, so evaluations may vary slightly between runs.
•	Critic calibration is prompt-based and may require further tuning.
•	SQLite is used for local development, not production-scale deployment.
•	Batch arbitration processes requests sequentially.
•	The Streamlit dashboard assumes the FastAPI backend is running locally.

Future Improvements

•	Add pytest test suite
•	Add Docker support
•	Add LangGraph workflow orchestration
•	Add retry logic for invalid LLM JSON
•	Add stronger structured output enforcement
•	Add user authentication
•	Add export to CSV/JSON
•	Deploy backend and dashboard
•	Add more critic types, such as safety, citation quality, and helpfulness
•	Add comparison mode for multiple LLM answers
