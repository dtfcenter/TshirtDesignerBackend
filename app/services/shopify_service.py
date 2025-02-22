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
            print("\n=== Debug Product Data ===")
            print("Product Data Keys:", product_data.keys())  # Hangi anahtarlar var görelim
            print("Full Product Data:", json.dumps(product_data, indent=2))  # Tüm veriyi görelim
            
            if 'sizes' not in product_data:
                print("Warning: 'sizes' key not found in product_data")
                return {
                    'success': False,
                    'error': "Missing required field: sizes"
                }
            
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

            # Görselleri hazırla ve yükle
            images = []
            image_id_map = {}  # Renk-görsel ID eşleştirmesi için
            
            for color in product_data['colors']:
                if color.get('mockupFront'):
                    try:
                        print(f"\n=== Processing Image for {color['name']} ===")
                        
                        if isinstance(color['mockupFront'], dict):
                            image_data = color['mockupFront']
                            images.append(image_data)
                            print(f"✅ Image processed for {color['name']}")
                        
                    except Exception as e:
                        print(f"❌ Error processing image: {str(e)}")

            # Önce ürünü ve görselleri oluştur
            initial_payload = {
                "product": {
                    "title": product_data['title'],
                    "body_html": product_data['description'],
                    "vendor": "T-Shirt Design Platform",
                    "product_type": "T-Shirt",
                    "options": [
                        {
                            'name': 'Size',
                            'position': 1,
                            'values': [s['value'] for s in product_data['sizes']]
                        },
                        {
                            'name': 'Color',
                            'position': 2,
                            'values': [c['name'] for c in product_data['colors']]
                        }
                    ],
                    "variants": [
                        {
                            'option1': size['value'],
                            'option2': color['name'],
                            'price': str(size['price']),
                            'requires_shipping': True,
                            'taxable': True,
                            'inventory_management': 'shopify',
                            'inventory_policy': 'continue',
                            'inventory_quantity': 100
                        }
                        for size in product_data['sizes']
                        for color in product_data['colors']
                    ],
                    "images": [
                        {
                            **image_data,
                            "variant_ids": []  # Varyant ID'leri sonra eklenecek
                        }
                        for color in product_data['colors']
                        if (image_data := color.get('mockupFront'))
                    ]
                }
            }

            # Ürünü oluştur
            response = requests.post(
                f"{shop_url}/products.json",
                json=initial_payload,
                headers=headers
            )
            
            if response.status_code != 201:
                raise Exception(f"Product creation failed: {response.text}")

            created_product = response.json()['product']
            
            # Görsel-varyant eşleştirmesi
            variant_map = {}
            for variant in created_product['variants']:
                color_name = variant['option2']  # Color option
                variant_map.setdefault(color_name, []).append(variant['id'])

            # Görselleri güncelle
            for image in created_product['images']:
                if 'alt' in image and ' - Front View' in image['alt']:
                    color_name = image['alt'].replace(' - Front View', '')
                    if color_name in variant_map:
                        # Görseli ilgili varyantlarla eşleştir
                        update_response = requests.put(
                            f"{shop_url}/products/{created_product['id']}/images/{image['id']}.json",
                            json={
                                "image": {
                                    "id": image['id'],
                                    "variant_ids": variant_map[color_name]
                                }
                            },
                            headers=headers
                        )
                        print(f"Updated image for {color_name} with variants: {variant_map[color_name]}")

            return {
                'success': True,
                'product_id': created_product['id'],
                'shopify_url': f"https://{store_name}.myshopify.com/products/{created_product['handle']}"
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