import os
import sqlite3
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def load_data():
    dataset_path = os.path.join(BASE_DIR, "dataset", "youtube_comments_sentiment_10000.csv")
    if not os.path.exists(dataset_path):
        dataset_path = "dataset/youtube_comments_sentiment_10000.csv"
    
    df = pd.read_csv(dataset_path)
    
    db_path = os.path.join(BASE_DIR, "app", "feedback.db")
    if not os.path.exists(db_path):
        db_path = "app/feedback.db"

    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        try:
            feedback_df = pd.read_sql_query("SELECT comment, sentiment FROM feedback", conn)
            if not feedback_df.empty:
                print(f"Loaded {len(feedback_df)} user feedback entries for retraining.")
                df = pd.concat([df, feedback_df], ignore_index=True)
        except Exception as e:
            print(f"No feedback loaded: {e}")
        finally:
            conn.close()
            
    return df

def train():
    df = load_data()
    X = df["comment"]
    y = df["sentiment"]

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
        ('clf', LogisticRegression(max_iter=1000))
    ])

    pipeline.fit(X, y)

    models_dir = os.path.join(BASE_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, "sentiment_model.pkl")
    joblib.dump(pipeline, model_path)
    print(f"Model saved successfully to {model_path}")

if __name__ == "__main__":
    train()