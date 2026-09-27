# YT Sentiment MLOps

A simple YouTube sentiment analysis MLOps project skeleton.

## Structure

- `app/` contains the FastAPI application.
- `ml/` contains model training and evaluation scripts.
- `models/` stores trained model artifacts.
- `tests/` contains API and Selenium-related tests.

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run tests

```bash
pytest -q
```
