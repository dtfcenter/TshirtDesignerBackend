# utils/image_processor.py
from PIL import Image
import os
from typing import Dict
from fastapi import UploadFile
import aiofiles
import uuid

# def convert_to_webp(image_path, quality=80):
#     try:
#         output_path = os.path.splitext(image_path)[0] + ".webp"
#         image = Image.open(image_path)
#         image.save(output_path, "webp", quality=quality)
#         os.remove(image_path)  # Orijinal PNG'yi sil
#         return output_path
#     except Exception as e:
#         print(f"⚠️ WebP Dönüşüm Hatası: {str(e)}")
#         return image_path  # Orjinal path'i döndür

async def convert_to_webp(file: UploadFile) -> Dict[str, str]:
    """
    Yüklenen dosyayı işleyip t-shirt mockup'ına yerleştirir
    """
    temp_path = None
    try:
        print("🔍 İşlem başlıyor...")
        
        # Geçici dosya oluştur
        temp_path = f"temp_{uuid.uuid4()}.png"
        print(f"📁 Geçici dosya: {temp_path}")
        
        # Mockup yolunu kontrol et
        mockup_path = os.path.join("src", "assets", "mockups", "white-front.png")
        print(f"👕 Mockup yolu: {mockup_path}")
        print(f"👕 Mockup var mı? {os.path.exists(mockup_path)}")
        
        if not os.path.exists(mockup_path):
            raise FileNotFoundError(f"Mockup bulunamadı: {mockup_path}")
            
        # Dosyayı kaydet
        async with aiofiles.open(temp_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        # Design'ı aç
        design = Image.open(temp_path).convert("RGBA")
        
        # Mockup'ı aç
        mockup = Image.open(mockup_path).convert("RGBA")
        
        # Design'ı küçült
        max_size = (800, 800)
        design.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Design'ı mockup üzerinde ortalamak için pozisyon hesapla
        mockup_width, mockup_height = mockup.size
        design_width, design_height = design.size
        
        # Design'ı mockup'ın %40'ı kadar genişlikte olacak şekilde yeniden boyutlandır
        new_width = int(mockup_width * 0.4)
        new_height = int(new_width * (design_height / design_width))
        design = design.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Yeni pozisyonu hesapla
        x = (mockup_width - new_width) // 2
        y = (mockup_height - new_height) // 3
        
        # Design'ı mockup üzerine yerleştir
        result = mockup.copy()
        result.paste(design, (x, y), design)
        
        # Sonucu kaydet
        output_path = os.path.join("uploads", f"result_{uuid.uuid4()}.webp")
        result.save(output_path, "WEBP", quality=90)
        
        # URL'i oluştur
        file_url = f"http://localhost:8000/uploads/{os.path.basename(output_path)}"
        
        # Temizlik
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {"mockup": file_url}
        
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise e