import os
import sqlite3
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.scraper import YouTubeScraper
from app.model_wrapper import ModelWrapper

app = FastAPI(
    title="YT Sentiment MLOps API",
    description="API and UI for YouTube video comment scraping and sentiment analysis",
    version="1.0.0"
)

# Base directories
BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.path.join(BASE_DIR, "feedback.db")

# Mount static files
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize modules
scraper = YouTubeScraper()
model_wrapper = ModelWrapper(model_path="models/sentiment_model.pkl")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


init_db()


# Pydantic schemas
class ReviewRequest(BaseModel):
    url: str
    max_comments: Optional[int] = 25


class PredictRequest(BaseModel):
    text: str


class FeedbackRequest(BaseModel):
    text: Optional[str] = None
    comment: Optional[str] = None
    corrected_sentiment: Optional[str] = None
    sentiment: Optional[str] = None


@app.get("/")
def read_root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "YT Sentiment MLOps API is running"}


@app.get("/api")
def api_info():
    return {"message": "YT Sentiment MLOps API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/review")
def review_url(payload: ReviewRequest):
    """
    Scrape top 20-25 comments from a YouTube URL and perform sentiment analysis.
    """
    url = payload.url
    max_comments = payload.max_comments or 25

    scrape_result = scraper.fetch_comments(url=url, max_comments=max_comments)
    comments = scrape_result.get("comments", [])

    analysis = model_wrapper.predict_batch(comments)

    return {
        "status": "success",
        "video_id": scrape_result.get("video_id"),
        "url": url,
        "scraped_comments_count": len(comments),
        "scrape_status": scrape_result.get("status"),
        "sentiment_analysis": analysis
    }


@app.get("/review_get")
def review_url_get(url: str, max_comments: int = 25):
    """GET endpoint variant for quick testing in browser or curl."""
    req = ReviewRequest(url=url, max_comments=max_comments)
    return review_url(req)


@app.post("/predict")
def predict_single(payload: PredictRequest):
    return model_wrapper.predict(payload.text)


@app.post("/feedback")
def submit_feedback(payload: FeedbackRequest):
    comment_text = payload.comment or payload.text
    sentiment_label = payload.sentiment or payload.corrected_sentiment

    if not comment_text or not sentiment_label:
        raise HTTPException(
            status_code=400,
            detail="Both comment/text and sentiment/corrected_sentiment are required."
        )

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback (comment, sentiment) VALUES (?, ?)",
            (comment_text, sentiment_label)
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Feedback saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")
