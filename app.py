from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
import os

# FastAPI uygulamasını oluştur
app = FastAPI(title="Printed T-Shirt Web")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", 
                  "http://localhost:3003", "http://localhost:3004", "http://localhost:3005", 
                  "http://localhost:3006"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Statik dosyalar için uploads klasörünü mount et
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    return {"message": "Printed T-Shirt Web API"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Gelen dosyayı kaydet
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_location = f"{upload_dir}/{file.filename}"
        with open(file_location, "wb+") as file_object:
            content = await file.read()
            file_object.write(content)

        try:
            # Template dosyasının tam yolunu yazdır
            template_path = os.path.join(os.getcwd(), "src/assets/mockups/white-front.png")
            print(f"Looking for template at: {template_path}")
            
            # T-shirt mockup'ı oluştur
            template = Image.open(template_path)
            design = Image.open(file_location)

            # T-shirt'in ön kısmına uygun boyut - çok daha büyük
            target_width = int(template.width * 0.5)  # T-shirt genişliğinin yarısı kadar
            target_height = int(template.height * 0.4)  # T-shirt yüksekliğinin %40'ı kadar

            # Orijinal oranı koru
            design_ratio = design.width / design.height
            if design_ratio > 1:  # Yatay tasarım
                new_width = target_width
                new_height = int(target_width / design_ratio)
            else:  # Dikey tasarım
                new_height = target_height
                new_width = int(target_height * design_ratio)

            # Tasarımı yeniden boyutlandır
            design = design.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # T-shirt üzerindeki pozisyonu ayarla
            # Tasarımı göğüs hizasında konumlandır
            position = (
                (template.width - design.width) // 2,  # Yatayda ortala
                int(template.height * 0.25)  # Üstten %25 aşağıda
            )

            # Tasarımı t-shirt'e yapıştır
            template.paste(design, position, design if design.mode == 'RGBA' else None)

            # Sonucu kaydet
            mockup_filename = f"mockup_{file.filename}"
            mockup_path = f"{upload_dir}/{mockup_filename}"
            template.save(mockup_path, "PNG")

            return {
                "success": True,
                "file_path": f"/uploads/{mockup_filename}"
            }
        except Exception as e:
            print(f"Mockup creation error: {str(e)}")
            raise e

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# Bu satırı ekleyin
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)