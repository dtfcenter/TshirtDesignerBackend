from fastapi import APIRouter, UploadFile, File
from .image_processor import convert_to_webp
import os

router = APIRouter()

@router.post("/upload/")
async def upload_design(file: UploadFile = File(...)):
    try:
        print("📥 Dosya alındı:", file.filename)  # Debug log
        result = await convert_to_webp(file)
        print("✅ İşlem sonucu:", result)  # Debug log
        
        if result and "mockup" in result:
            return {"success": True, "file_path": result["mockup"]}
        else:
            return {"success": False, "error": "Mockup oluşturulamadı"}
            
    except Exception as e:
        print("❌ Hata:", str(e))  # Debug log
        return {"success": False, "error": str(e)}
    finally:
        if hasattr(file, "file"):
            file.file.close() 