# DiViz API (FastAPI) and a SPA (Next.js)

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

Load the UI from http://localhost:8000/static/index.html 

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


## API Documentation

Once the service is running, you can access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deploying to AWS

This repo includes an AWS CDK app under `cdk/` that deploys the API behind API Gateway, Lambda, and Cognito. For prerequisites, first-time setup, and the optimized `./deploy.sh` workflow, follow the step-by-step guide in `cdk/README.md`.

## Analyzing a meeting transcript

The `analyzer.py` script can be used to analyze a meeting transcript. It takes two arguments:
- agenda_file: Path to the agenda JSON file
- transcript_file: Path to the transcript JSON file

Example:
```bash
python analyzer.py agenda.json transcript.json
```

The `analyzer_api.py` script can be used to analyze a meeting transcript via the API.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

Copyright (c) 2025 Konstantyn Novoselov
