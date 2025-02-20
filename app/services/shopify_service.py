from typing import Dict
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import asyncio
import base64
import requests
import json

load_dotenv()

class ShopifyService:
    def __init__(self):
        # Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

        print("Debug - SUPABASE_URL:", supabase_url)
        print("Debug - SUPABASE_KEY:", supabase_key)

        # Supabase bağlantısı
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")

        # URL'in doğru formatta olduğundan emin ol
        if not supabase_url.startswith('https://'):
            supabase_url = f'https://{supabase_url}'

        self.supabase: Client = create_client(
            supabase_url,
            supabase_key
        )

    def create_product(self, product_data: Dict) -> Dict:
        try:
            print("\n=== Shopify Ürün Oluşturma Detayları ===")
            print("Gönderilen ürün verisi:", json.dumps(product_data, indent=2))
            
            # Shopify API endpoint ve headers
            store_name = os.getenv('SHOPIFY_SHOP_URL')
            access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
            shop_url = f"https://{store_name}.myshopify.com/admin/api/2024-01"
            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            }

            # Görselleri hazırla
            images = []
            for color in product_data['colors']:
                if color.get('mockupFront'):
                    try:
                        print(f"\n=== Processing Image ===")
                        print(f"Color: {color['name']}")
                        
                        # Eğer mockupFront zaten bir dictionary ise
                        if isinstance(color['mockupFront'], dict):
                            images.append(color['mockupFront'])
                            print("✅ Image data already in correct format")
                        else:
                            print("❌ Invalid image format")
                            
                    except Exception as e:
                        print(f"❌ Error processing image: {str(e)}")
                        print(f"Error type: {type(e)}")

            print(f"\nTotal images to process: {len(product_data['colors'])}")
            print(f"Successfully processed images: {len(images)}")

            # Varyantları hazırla
            variants = []
            for size in product_data['sizes']:
                for color in product_data['colors']:
                    variants.append({
                        'option1': size['value'],  # Beden
                        'option2': color['name'],  # Renk
                        'price': str(size['price']),
                        'requires_shipping': True,
                        'taxable': True,
                        'inventory_management': 'shopify',
                        'inventory_policy': 'continue',
                        'inventory_quantity': 100
                    })

            # Ürün verisi
            product_payload = {
                "product": {
                    "title": product_data['title'],
                    "body_html": product_data['description'],
                    "vendor": "T-Shirt Design Platform",
                    "product_type": "T-Shirt",
                    "images": images,
                    "variants": variants,
                    "options": [
                        {'name': 'Size', 'values': list(set(s['value'] for s in product_data['sizes']))},
                        {'name': 'Color', 'values': list(set(c['name'] for c in product_data['colors']))}
                    ]
                }
            }

            print("\n=== Shopify Request ===")
            print(f"Images in payload: {len(product_payload['product']['images'])}")
            print("First image data:", product_payload['product']['images'][0] if images else "No images")
            print("Image structure:", [
                {
                    'name': color['name'],
                    'mockup_front': color.get('mockup_front', '')[:100] + '...' if color.get('mockup_front') else None
                } for color in product_data['colors']
            ])

            # Shopify'a gönder
            print("Sending request to Shopify...")
            response = requests.post(
                f"{shop_url}/products.json",
                json=product_payload,
                headers=headers
            )

            print("Shopify API yanıtı:", response.text)
            print("Yanıt kodu:", response.status_code)
            
            if not response.ok:
                print("Hata detayı:", response.json())
            
            if response.status_code == 201:
                data = response.json()
                return {
                    'success': True,
                    'product_id': data['product']['id'],
                    'shopify_url': f"https://{store_name}.myshopify.com/products/{data['product']['handle']}"
                }
            else:
                return {
                    'success': False,
                    'error': f"Shopify API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            print("Ürün oluşturma hatası:", str(e))
            print("Hata tipi:", type(e))
            print("Hata detayları:", getattr(e, 'details', 'Detay yok'))
            raise e

    async def get_products_by_ids(self, product_ids: list):
        try:
            print("Fetching products with IDs:", product_ids)
            
            # Önce product_sizes tablosunu kontrol et
            sizes_data = self.supabase.table('product_sizes').select('*').in_('product_id', product_ids).execute()
            print("Sizes data:", sizes_data.data)
            
            # Sonra product_colors tablosunu kontrol et
            colors_data = self.supabase.table('product_colors').select('*').in_('product_id', product_ids).execute()
            print("Colors data:", colors_data.data)
            
            # Ana ürün verisini al
            data = self.supabase.table('products').select('*').in_('id', product_ids).execute()
            
            # Veriyi birleştir
            products = []
            for product in data.data:
                product_sizes = [s for s in sizes_data.data if s['product_id'] == product['id']]
                product_colors = [c for c in colors_data.data if c['product_id'] == product['id']]
                
                if not product_sizes:
                    print(f"Warning: No sizes found for product {product['id']}")
                    continue
                    
                if not product_colors:
                    print(f"Warning: No colors found for product {product['id']}")
                    continue
                    
                products.append({
                    'id': product['id'],
                    'title': product['title'],
                    'description': product.get('description', ''),
                    'sizes': [
                        {
                            'value': size['value'],
                            'price': float(size['price'])
                        } for size in product_sizes
                    ],
                    'colors': [
                        {
                            'name': color['name'],
                            'mockup_front': color.get('mockup_front', '')
                        } for color in product_colors
                    ]
                })
            
            print("Processed products:", products)
            return products
            
        except Exception as e:
            print("Error fetching products:", str(e))
            raise e

    async def upload_to_shopify(self, products: list):
        try:
            print("\n=== Starting Shopify Upload ===")
            print(f"Total products to upload: {len(products)}")
            
            results = []
            for product in products:
                print("\n--- Processing Product ---")
                print(f"Title: {product['title']}")
                print("Product data:", product)  # Tüm ürün verisini göster
                
                # Her ürün için Shopify'a yükleme yap
                try:
                    result = self.create_product({
                        'title': product['title'],
                        'description': product.get('description', ''),
                        'sizes': [
                            {
                                'value': str(size['value']),  # String'e çevir
                                'price': str(size['price'])   # String'e çevir
                            } for size in product.get('sizes', [])
                        ],
                        'colors': [
                            {
                                'name': color['name'],
                                'mockupFront': {
                                    'attachment': color['mockup_front'].split(',')[-1] if color.get('mockup_front') else None,
                                    'filename': f"{color['name']}_front.png",
                                    'alt': f"{color['name']} - Front View"
                                } if color.get('mockup_front') else None
                            } for color in product.get('colors', [])
                        ]
                    })
                    
                    print("Create product result:", result)
                    results.append({
                        'product_id': product['id'],
                        'title': product['title'],
                        'shopify_result': result
                    })
                except Exception as product_error:
                    print(f"Error processing product {product['title']}: {str(product_error)}")
                    results.append({
                        'product_id': product['id'],
                        'title': product['title'],
                        'error': str(product_error)
                    })
                
                await asyncio.sleep(1)
            
            print("\n=== Upload Results ===")
            print(results)
            return results
            
        except Exception as e:
            print("Error uploading to Shopify:", str(e))
            print("Error type:", type(e))
            print("Error details:", getattr(e, 'details', 'No details'))
            raise e 