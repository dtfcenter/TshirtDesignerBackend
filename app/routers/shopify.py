from fastapi import APIRouter, HTTPException
from ..services.shopify_service import ShopifyService

router = APIRouter()
shopify_service = ShopifyService()

@router.post("/upload-products")
async def upload_products(request: dict):
    try:
        product_ids = request.get('productIds', [])
        
        # Önce ürünleri Supabase'den al
        products = await shopify_service.get_products_by_ids(product_ids)
        
        # Sonra Shopify'a yükle
        results = await shopify_service.upload_to_shopify(products)
        
        return {"success": True, "results": results}
        
    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e)) 