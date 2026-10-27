
# AgentOps

A local-first observability platform for monitoring AI agent executions.

## Overview

AgentOps collects structured events from agent runs, stores them in SQLite,
and exposes a FastAPI API for exploring traces and execution metrics.
A Streamlit dashboard presents event statistics, duration charts, and trace details.

## Features

- REST API for agent event ingestion
- SQLite persistence
- Trace lookup and summary endpoints
- Event analytics, including success and failure counts
- Simulated agent for local testing
- Streamlit dashboard with filters and duration charts
- Automated API tests using pytest

## Tech Stack

- Python
- FastAPI
- Pydantic
- SQLite
- Streamlit
- Pandas
- HTTPX
- Pytest

## Local Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the API from the project root:

```bash
uvicorn app.main:app --reload
```

Open the API documentation:

http://127.0.0.1:8000/docs

In a second terminal, start the dashboard:

```bash
python -m streamlit run dashboard.py
```

Run the tests:

```bash
python -m pytest -v
```

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check API status |
| POST | `/events` | Record an event |
| GET | `/events` | List or filter events |
| GET | `/events/{event_id}` | Retrieve one event |
| GET | `/analytics` | View event metrics |
| GET | `/traces/{trace_id}` | View a trace summary |

## Current Limitations

- Agent execution is simulated; no real LLM integration yet.
- Authentication and multi-user access are not implemented.
- SQLite is intended for local development in this version.
- Trace duration requires valid start and end events.

## Roadmap

- Add real agent instrumentation
- Improve trace lifecycle and error handling
- Add authentication and API-key support
- Add evaluation metrics for agent outputs
- Improve dashboard usability
