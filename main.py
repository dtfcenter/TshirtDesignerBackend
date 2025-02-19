from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from utils import auth
from database import Base, engine
import uvicorn
from dotenv import load_dotenv

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Printed T-Shirt Web")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Geçici dosyalar için uploads klasörü
os.makedirs("uploads", exist_ok=True)

# Statik dosya servisini ayarla
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/mockups", StaticFiles(directory="src/assets/mockups"), name="mockups")

# Upload router'ını import et
from utils.upload_router import router
app.include_router(router, prefix="/api")

app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Printed T-Shirt Web API"}

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info") 