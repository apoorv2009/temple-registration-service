# Temple Registration Service

FastAPI service for self-service and referred devotee signup requests.

## Responsibilities

- receive self-service signup requests
- receive referred signup requests from approved users
- prevent duplicate approved contact numbers later
- track request lifecycle

## Local run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload --port 8002
```

## Render start command

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

