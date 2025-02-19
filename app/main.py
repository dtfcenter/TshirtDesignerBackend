from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routers import upload  # router'ı import et
from .services.shopify_service import ShopifyService
from .models.product import ProductCreate

app = FastAPI(title="Printed T-Shirt Web")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ı ekle
app.include_router(upload.router, prefix="/api")

# Statik dosyalar için mockups klasörünü mount et
app.mount("/mockups", StaticFiles(directory="assets/mockups"), name="mockups")

router = APIRouter()
shopify_service = ShopifyService()

@router.post("/products/publish-to-shopify")
async def publish_to_shopify(product: ProductCreate):
    result = shopify_service.create_product(product.dict())
    return result

@app.get("/")
async def root():
    return {"message": "Printed T-Shirt Web API"}

# Router'ı /api prefix'i ile ekle
app.include_router(router, prefix="/api") 