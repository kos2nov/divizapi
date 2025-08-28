# DiViz API (FastAPI)

A small FastAPI service with a root info endpoint and a simple review endpoint.

## Prerequisites

- Python 3.11 or higher
- uv (Ultra-fast Python package installer and resolver)

Install uv if you haven't already:
```bash
pip install uv
```

## Installation

1) Install dependencies using uv:
```bash
uv sync
```

2) For development dependencies (includes testing tools):
```bash
uv sync --dev
```

## Running the Service

- Run with uvicorn via uv:
```bash
uv run uvicorn diviz.main:app --host 0.0.0.0 --port 8000 --reload
```

- Or run the module directly (uses the built-in main() which starts uvicorn):
```bash
uv run python -m diviz.main
```

The service will be available at http://localhost:8000

## Testing

### Run tests
```bash
uv run pytest -v
```

### With coverage report
```bash
uv run pytest --cov=diviz --cov-report=term --cov-report=html
```

### Run a specific test file
```bash
uv run pytest tests/test_api.py
```

### Using the test runner script
```bash
python run_tests.py
```

## Test Structure

- tests/test_api.py — Integration tests for FastAPI endpoints
- tests/conftest.py — Shared pytest fixtures and configuration

## API Endpoints

### GET /
Returns service information and available endpoints.

Example response:
```json
{
  "service": "Echo Service",
  "version": "1.0.0",
  "endpoints": {
    "/review": "GET - meeting review"
  }
}
```

### GET /review/gmeet/{google_meet}
Returns the provided Google Meet code for demonstration.

Example:
```bash
curl "http://localhost:8000/review/gmeet/abc-defg-hjk"
```
Response:
```json
{
  "meeting_code": "abc-defg-hjk"
}
```

## API Documentation

Once the service is running, you can access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deploying to AWS (optional)

This repo includes an AWS CDK app under `cdk/` that deploys the API behind API Gateway and Lambda. See `cdk/README.md` for details and scripts.
