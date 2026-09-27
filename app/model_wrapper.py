import os
import joblib

class ModelWrapper:
    def __init__(self, model_path: str = "models/sentiment_model.pkl"):
        self.model_path = model_path
        self.model = self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                return joblib.load(self.model_path)
            except Exception as e:
                print(f"Error loading model from {self.model_path}: {e}")
                return None
        else:
            print(f"Warning: Model not found at {self.model_path}")
            return None

    def predict(self, text: str) -> dict:
        if not text:
            return {"text": text, "sentiment": "neutral"}

        if self.model:
            try:
                pred = self.model.predict([text])[0]
                return {"text": text, "sentiment": str(pred)}
            except Exception as e:
                print(f"Prediction error: {e}")

        # Baseline fallback heuristics if model is not loaded
        lowered = text.lower()
        if any(w in lowered for w in ["great", "awesome", "good", "love", "amazing", "thanks", "helpful"]):
            sentiment = "positive"
        elif any(w in lowered for w in ["bad", "worst", "terrible", "boring", "dislike", "hate"]):
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {"text": text, "sentiment": sentiment}

    def predict_batch(self, comments: list[str]) -> dict:
        if not comments:
            return {
                "total_comments": 0,
                "summary": {"positive": 0, "negative": 0, "neutral": 0},
                "percentage": {"positive": 0.0, "negative": 0.0, "neutral": 0.0},
                "overall_sentiment": "neutral",
                "predictions": []
            }

        predictions = []
        counts = {"positive": 0, "negative": 0, "neutral": 0}

        for comment in comments:
            res = self.predict(comment)
            predictions.append(res)
            sentiment = res["sentiment"].lower()
            counts[sentiment] = counts.get(sentiment, 0) + 1

        total = len(comments)
        percentages = {
            k: round((v / total) * 100, 2) for k, v in counts.items()
        }

        # Determine overall sentiment
        dominant = max(counts, key=counts.get)

        return {
            "total_comments": total,
            "summary": counts,
            "percentage": percentages,
            "overall_sentiment": dominant,
            "predictions": predictions
        }
