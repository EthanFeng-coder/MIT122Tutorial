from fastapi import FastAPI
from upload_handler import router as upload_router

app = FastAPI()
app.include_router(upload_router)
@app.get("/")
def root():
    return {"message": "Server is running"}


