from fastapi import FastAPI

app = FastAPI(title="YT Sentiment MLOps")


@app.get("/")
def read_root():
    return {"message": "YT Sentiment MLOps API is running"}
