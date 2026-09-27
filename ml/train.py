import os
import sqlite3
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

def load_data():
    df = pd.read_csv("dataset/youtube_comments_sentiment_10000.csv")
    db_path = "yt-sentiment-mlops/app/feedback.db"
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        try:
            feedback_df = pd.read_sql_query("SELECT comment, sentiment FROM feedback", conn)
            if not feedback_df.empty:
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
        ('clf', LogisticRegression())
    ])

    pipeline.fit(X, y)

    os.makedirs("models", exist_ok=True)
    model_path = "models/sentiment_model.pkl"
    joblib.dump(pipeline, model_path)
    print(f"Model saved successfully to {model_path}")

if __name__ == "__main__":
    train()