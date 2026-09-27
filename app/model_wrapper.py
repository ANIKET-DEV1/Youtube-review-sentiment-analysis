class ModelWrapper:
    def __init__(self, model_path: str = "models/sentiment_model.pkl"):
        self.model_path = model_path

    def predict(self, text: str):
        return {"text": text, "label": "neutral"}
