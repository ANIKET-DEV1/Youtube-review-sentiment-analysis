from fastapi import FastAPI

app = FastAPI(title="YT Sentiment MLOps")


@app.get("/")
def read_root():
    return {"message": "YT Sentiment MLOps API is running"}

@app.post("/review")
def review_rank(url:str):
    
    return "pass"
