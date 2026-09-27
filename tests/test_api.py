from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.scraper import YouTubeScraper

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "YT Sentiment" in response.text

def test_api_info_endpoint():
    response = client.get("/api")
    assert response.status_code == 200
    assert "running" in response.json()["message"]

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_predict_endpoint():
    payload = {"text": "Great video explanation!"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "sentiment" in data

def test_feedback_endpoint():
    payload = {
        "text": "Great video explanation!",
        "corrected_sentiment": "positive"
    }
    response = client.post("/feedback", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@patch.object(YouTubeScraper, 'fetch_comments')
def test_review_endpoint(mock_fetch):
    mock_fetch.return_value = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "video_id": "dQw4w9WgXcQ",
        "count": 3,
        "comments": [
            "Great explanation!",
            "Terrible quality.",
            "It was okay."
        ],
        "status": "success"
    }

    payload = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "max_comments": 25
    }
    response = client.post("/review", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "sentiment_analysis" in data
    assert data["sentiment_analysis"]["total_comments"] == 3

def test_scraper_video_id_extraction():
    scraper = YouTubeScraper()
    assert scraper.extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert scraper.extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert scraper.extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert scraper.extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"