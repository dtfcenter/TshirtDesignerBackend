from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Supabase bağlantısı
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

@router.post("/upload-products")
async def upload_products(request: dict):
    try:
        product_ids = request.get('productIds', [])
        
        # Test amaçlı önce sadece verileri çekelim
        data = supabase.table('products').select("""
            *,
            sizes:product_sizes (value, price),
            colors:product_colors (name, mockup_front, mockup_back)
        """).in_('id', product_ids).execute()
        
        # Şimdilik sadece çektiğimiz verileri loglayalım
        print("Fetched products:", data.data)
        
        return {"success": True, "message": f"Received {len(product_ids)} product IDs"}
        
    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e)) 