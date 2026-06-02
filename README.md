# LLM Output Arbitration System

An AI Engineering portfolio project that evaluates LLM-generated answers using multiple critic agents, disagreement detection, and an LLM adjudicator.

## Running the API

```bash
source venv/bin/activate
uvicorn app.api:app --reload
```

API docs available at: http://127.0.0.1:8000/docs

## Running the Streamlit dashboard

```bash
source venv/bin/activate
streamlit run streamlit_app.py
```

Requires the FastAPI backend to be running in a separate terminal.
