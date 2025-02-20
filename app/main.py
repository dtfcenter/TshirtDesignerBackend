from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from .routers import shopify  # sadece shopify router'ı
from .services.shopify_service import ShopifyService

# .env dosyasını yükle
load_dotenv()

# Environment değişkenlerini kontrol et
print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("SUPABASE_SERVICE_KEY:", os.getenv("SUPABASE_SERVICE_KEY"))

app = FastAPI(title="Printed T-Shirt Web")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tshirt-designer-frontend.vercel.app",
        "https://yourdomain.com"  # Domain alındığında eklenecek
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()
shopify_service = ShopifyService()

@app.get("/")
async def root():
    return {"message": "Printed T-Shirt Web API"}

# Router'ı /api prefix'i ile ekle
app.include_router(router, prefix="/api")

# Shopify router'ını ekle
app.include_router(shopify.router, prefix="/api/shopify", tags=["shopify"]) 