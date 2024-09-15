# shopify_order_variant_image_test.py

import os
import requests
from dotenv import load_dotenv

def load_credentials():
    """
    Load Shopify credentials from the .env file.
    """
    load_dotenv()
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    store_url = os.getenv("SHOPIFY_STORE_URL")
    
    if not access_token or not store_url:
        raise ValueError("Missing SHOPIFY_ACCESS_TOKEN or SHOPIFY_STORE_URL in the .env file.")
    
    return access_token, store_url

def get_order_details(access_token, store_url, order_id):
    """
    Fetch order details from Shopify using order_id.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }
    url = f"https://{store_url}/admin/api/2023-10/orders/{order_id}.json"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("order", {})
    elif response.status_code == 404:
        print(f"Order with ID {order_id} not found.")
        return None
    else:
        print(f"HTTP Error {response.status_code} while fetching order {order_id} details.")
        print(response.text)
        return None

def get_variant_image(access_token, store_url, variant_id):
    """
    Fetch variant image URL from Shopify.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }
    url = f"https://{store_url}/admin/api/2023-10/variants/{variant_id}.json"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        variant = response.json().get("variant", {})
        image_id = variant.get("image_id")
        
        if image_id:
            # Fetch image details
            image_url = get_image_url(access_token, store_url, image_id)
            return image_url
        else:
            # Fallback to product's default image
            product_id = variant.get("product_id")
            if product_id:
                default_image_url = get_product_default_image(access_token, store_url, product_id)
                return default_image_url
            else:
                print(f"No product_id found for variant {variant_id}.")
                return None
    elif response.status_code == 404:
        print(f"Variant with ID {variant_id} not found.")
        return None
    else:
        print(f"HTTP Error {response.status_code} while fetching variant {variant_id} details.")
        print(response.text)
        return None

def get_image_url(access_token, store_url, image_id):
    """
    Fetch image URL from Shopify using image_id.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }
    url = f"https://{store_url}/admin/api/2023-10/images/{image_id}.json"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        image = response.json().get("image", {})
        return image.get("src")
    elif response.status_code == 404:
        print(f"Image with ID {image_id} not found.")
        return None
    else:
        print(f"HTTP Error {response.status_code} while fetching image {image_id} details.")
        print(response.text)
        return None

def get_product_default_image(access_token, store_url, product_id):
    """
    Fetch the default image URL of a product from Shopify.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }
    url = f"https://{store_url}/admin/api/2023-10/products/{product_id}.json"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        product = response.json().get("product", {})
        images = product.get("images", [])
        if images:
            return images[0].get("src")  # Return the first image as default
        else:
            print(f"No images found for product ID {product_id}.")
            return None
    elif response.status_code == 404:
        print(f"Product with ID {product_id} not found.")
        return None
    else:
        print(f"HTTP Error {response.status_code} while fetching product {product_id} details.")
        print(response.text)
        return None

def main():
    try:
        access_token, store_url = load_credentials()
    except ValueError as ve:
        print(ve)
        return
    
    order_id_input = input("Enter the Shopify Order ID to test: ").strip()
    
    if not order_id_input.isdigit():
        print("Invalid Order ID. It should be a numeric value.")
        return
    
    order_id = int(order_id_input)
    
    print(f"\nFetching details for Order ID: {order_id}...")
    order = get_order_details(access_token, store_url, order_id)
    
    if not order:
        return
    
    print(f"\nOrder ID: {order.get('id')}")
    print(f"Order Name: {order.get('name')}")
    print(f"Customer: {order.get('customer', {}).get('first_name', '')} {order.get('customer', {}).get('last_name', '')}")
    print(f"Number of Line Items: {len(order.get('line_items', []))}\n")
    
    for idx, item in enumerate(order.get("line_items", []), start=1):
        variant_id = item.get("variant_id")
        product_title = item.get("title")
        variant_title = item.get("variant_title")
        quantity = item.get("quantity")
        
        print(f"Line Item {idx}:")
        print(f"  Product Title: {product_title}")
        print(f"  Variant Title: {variant_title}")
        print(f"  Variant ID: {variant_id}")
        print(f"  Quantity: {quantity}")
        
        if variant_id:
            image_url = get_variant_image(access_token, store_url, variant_id)
            if image_url:
                print(f"  Image URL: {image_url}\n")
            else:
                print(f"  Image URL: Not Available\n")
        else:
            print("  Variant ID not found.\n")

if __name__ == "__main__":
    main()
