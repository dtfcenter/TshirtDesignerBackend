import shopify
from typing import Dict
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import asyncio
import base64
import requests

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

            print(f"Shopify response status: {response.status_code}")
            print(f"Shopify response: {response.text[:200]}")

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
            print(f"❌ Create product error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_products_by_ids(self, product_ids: list):
        try:
            data = self.supabase.table('products').select("""
                *,
                sizes:product_sizes (value, price),
                colors:product_colors (name, mockup_front, mockup_back)
            """).in_('id', product_ids).execute()
            
            return data.data
        except Exception as e:
            print("Error fetching products:", str(e))
            raise e

    async def upload_to_shopify(self, products: list):
        try:
            results = []
            for product in products:
                print("\n--- Processing Product ---")
                print(f"Title: {product['title']}")
                
                # Her ürün için Shopify'a yükleme yap
                result = self.create_product({
                    'title': product['title'],
                    'description': product['description'],
                    'sizes': [
                        {
                            'value': size['value'],
                            'price': size['price']
                        } for size in product['sizes']
                    ],
                    'colors': [
                        {
                            'name': color['name'],
                            'mockupFront': {
                                'attachment': color['mockup_front'].split(',')[-1] if color.get('mockup_front') else None,  # base64 prefix'i kaldır
                                'filename': f"{color['name']}_front.png",
                                'alt': f"{color['name']} - Front View"
                            }
                        } for color in product['colors']
                    ]
                })
                
                print("Upload result:", result)
                results.append({
                    'product_id': product['id'],
                    'title': product['title'],
                    'shopify_result': result
                })
                
                await asyncio.sleep(1)
            
            return results
            
        except Exception as e:
            print("Error uploading to Shopify:", str(e))
            raise e 