from fastapi import FastAPI

app = FastAPI(title="SIH Border AI Backend")


@app.get("/")
def read_root():
    return {"message": "SIH Border AI Backend"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
