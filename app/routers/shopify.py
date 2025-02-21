from fastapi import APIRouter, HTTPException
from ..services.shopify_service import ShopifyService

router = APIRouter()

# Service'i router'da initialize et, main.py'da değil
shopify_service = None

def get_service():
    global shopify_service
    if shopify_service is None:
        shopify_service = ShopifyService()
    return shopify_service

@router.post("/upload-products")
async def upload_products(request: dict):
    try:
        service = get_service()  # Lazy initialization
        product_ids = request.get('productIds', [])
        
        # Önce ürünleri Supabase'den al
        products = await service.get_products_by_ids(product_ids)
        
        
        # Sonra Shopify'a yükle
        results = await service.upload_to_shopify(products)
        
        return {"success": True, "results": results}
        
    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e)) 
    
    