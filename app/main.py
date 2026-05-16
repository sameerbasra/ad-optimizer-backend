from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.google_ads import router as google_ads_router

app = FastAPI(title="AdOptimizer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://localhost:5175",
        "https://storied-bienenstitch-d70ff8.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(google_ads_router, prefix="/api/google-ads")

@app.get("/")
def root():
    return {"status": "AdOptimizer API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}