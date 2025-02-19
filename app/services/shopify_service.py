import shopify
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()

class ShopifyService:
    def __init__(self):
        # Shopify store name'i al ve URL'i oluştur
        store_name = os.getenv('SHOPIFY_SHOP_URL')
        shop_url = f"{store_name}.myshopify.com"
        access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        
        # API versiyonu ve access token ile session oluştur
        session = shopify.Session(shop_url, '2024-01', access_token)
        shopify.ShopifyResource.activate_session(session)

    def create_product(self, product_data: Dict) -> Dict:
        """
        Shopify'da yeni bir ürün oluşturur
        """
        try:
            new_product = shopify.Product()
            new_product.title = product_data['title']
            new_product.body_html = product_data['description']
            new_product.vendor = "T-Shirt Design Platform"
            new_product.product_type = "T-Shirt"
            
            # Varyantları oluştur (beden ve renk kombinasyonları)
            variants = []
            for size in product_data['sizes']:
                for color in product_data['colors']:
                    variant = shopify.Variant({
                        'option1': size['value'],  # Beden
                        'option2': color['name'],  # Renk
                        'price': str(size['price']),
                        'requires_shipping': True,
                        'taxable': True,
                        'inventory_management': 'shopify',
                        'inventory_policy': 'continue',
                        'inventory_quantity': 100  # Varsayılan stok
                    })
                    variants.append(variant)
            
            new_product.variants = variants
            
            # Ürün seçeneklerini tanımla
            new_product.options = [
                {'name': 'Size', 'values': list(set(s['value'] for s in product_data['sizes']))},
                {'name': 'Color', 'values': list(set(c['name'] for c in product_data['colors']))}
            ]
            
            # Mockup görsellerini ekle
            images = []
            for color in product_data['colors']:
                if color.get('mockupFront'):
                    image = shopify.Image({
                        'src': color['mockupFront'],
                        'alt': f"Front view - {color['name']}"
                    })
                    images.append(image)
                if color.get('mockupBack'):
                    image = shopify.Image({
                        'src': color['mockupBack'],
                        'alt': f"Back view - {color['name']}"
                    })
                    images.append(image)
            
            new_product.images = images
            
            # Ürünü kaydet
            if new_product.save():
                store_name = os.getenv('SHOPIFY_SHOP_URL')
                return {
                    'success': True,
                    'product_id': new_product.id,
                    'shopify_url': f"https://{store_name}.myshopify.com/products/{new_product.handle}"
                }
            else:
                return {
                    'success': False,
                    'errors': new_product.errors.full_messages()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            } 