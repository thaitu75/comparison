# order_comparison_app.py

import streamlit as st
import requests
import json
import pandas as pd
import os

# ==========================================
# 🔒 Configuration: Load Environment Variables
# ==========================================

# 🐟 Cat Kiss Fish API Credentials
CATKISSFISH_CLIENT_ID = os.getenv("CATKISSFISH_CLIENT_ID")
CATKISSFISH_CLIENT_SECRET = os.getenv("CATKISSFISH_CLIENT_SECRET")

# 🛍️ Shopify Stores Configuration
SHOPIFY_STORES = {
    'G': {
        'url': os.getenv("SHOPIFY_STORE_1_URL"),
        'access_token': os.getenv("SHOPIFY_STORE_1_ACCESS_TOKEN")
    },
    'C': {
        'url': os.getenv("SHOPIFY_STORE_2_URL"),
        'access_token': os.getenv("SHOPIFY_STORE_2_ACCESS_TOKEN")
    },
    'U': {
        'url': os.getenv("SHOPIFY_STORE_3_URL"),
        'access_token': os.getenv("SHOPIFY_STORE_3_ACCESS_TOKEN")
    }
}

# ==========================================
# 🌐 API Endpoints
# ==========================================

# 🐟 Cat Kiss Fish API Endpoints
CATKISSFISH_TOKEN_URL = "https://www.catkissfish.com:8443/oauth2/client_token"
CATKISSFISH_ORDER_DETAIL_URL = "https://www.catkissfish.com:8443/open/api/order/v1/order/detail"

# ==========================================
# 🚀 Functions to Interact with APIs
# ==========================================

import sys
import subprocess

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# 🐟 Function to get access token from Cat Kiss Fish
def get_catkissfish_access_token(client_id, client_secret):
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    try:
        response = requests.post(CATKISSFISH_TOKEN_URL, data=payload)
        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get("code") in [200, 0]:
                return resp_json["data"]["client_token"]
            else:
                st.error(f"Error obtaining Cat Kiss Fish token: {resp_json.get('msg')}")
                st.json(resp_json)  # Display full response for debugging
                return None
        else:
            st.error(f"HTTP Error {response.status_code} while obtaining Cat Kiss Fish token.")
            st.text(response.text)  # Display response text for debugging
            return None
    except Exception as e:
        st.error(f"Exception occurred while obtaining Cat Kiss Fish token: {e}")
        return None

# 🐟 Function to get order details from Cat Kiss Fish
def get_catkissfish_order_details(order_id, access_token):
    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "access_token": access_token
    }
    params = {
        "id": order_id
    }
    try:
        response = requests.get(CATKISSFISH_ORDER_DETAIL_URL, headers=headers, params=params)
        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get("code") in [200, 0]:
                return resp_json["data"]
            else:
                st.error(f"Cat Kiss Fish API Error: {resp_json.get('message')}")
                st.json(resp_json)  # Display full response for debugging
                return None
        else:
            st.error(f"HTTP Error {response.status_code} while fetching Cat Kiss Fish order details.")
            st.text(response.text)  # Display response text for debugging
            return None
    except Exception as e:
        st.error(f"Exception occurred while fetching Cat Kiss Fish order details: {e}")
        return None

# 🛍️ Function to get Shopify order details based on order name
def get_shopify_order_details(order_number, store_prefix):
    store = SHOPIFY_STORES.get(store_prefix.upper())
    if not store:
        st.error(f"No Shopify store configuration found for prefix '{store_prefix}'.")
        return []
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": store['access_token']
    }
    params = {
        "name": order_number
    }
    try:
        response = requests.get(f"https://{store['url']}/admin/api/2023-10/orders.json", headers=headers, params=params)
        if response.status_code == 200:
            resp_json = response.json()
            orders = resp_json.get("orders", [])
            if orders:
                # Filter out products containing "Versand" or "shipping" in the name
                filtered_orders = []
                for order in orders:
                    filtered_line_items = [
                        item for item in order.get("line_items", [])
                        if "versand" not in item.get("name", "").lower() and "shipping" not in item.get("name", "").lower()
                    ]
                    if filtered_line_items:
                        order["line_items"] = filtered_line_items
                        filtered_orders.append(order)
                if filtered_orders:
                    return filtered_orders  # Return all filtered orders (assuming unique order numbers)
                else:
                    st.error(f"All products in Shopify order {order_number} are excluded based on filtering criteria.")
                    return []
            else:
                st.error(f"No Shopify order found with Order Number: {order_number}")
                return []
        else:
            st.error(f"HTTP Error {response.status_code} while fetching Shopify order details.")
            st.text(response.text)  # Display response text for debugging
            return []
    except Exception as e:
        st.error(f"Exception occurred while fetching Shopify order details: {e}")
        return []

# 🛍️ Function to get Shopify variant image given a variant ID and store prefix
def get_shopify_variant_image(variant_id, store_prefix):
    store = SHOPIFY_STORES.get(store_prefix.upper())
    if not store:
        st.error(f"No Shopify store configuration found for prefix '{store_prefix}'.")
        return None
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": store['access_token']
    }
    try:
        # Fetch variant details
        variant_response = requests.get(f"https://{store['url']}/admin/api/2023-10/variants/{variant_id}.json", headers=headers)
        if variant_response.status_code == 200:
            variant = variant_response.json().get("variant", {})
            image_id = variant.get("image_id")
            product_id = variant.get("product_id")
            if image_id and product_id:
                # Fetch image details using product_id and image_id
                image_response = requests.get(f"https://{store['url']}/admin/api/2023-10/products/{product_id}/images/{image_id}.json", headers=headers)
                if image_response.status_code == 200:
                    image = image_response.json().get("image", {})
                    image_url = image.get("src")
                    return image_url
                else:
                    st.error(f"HTTP Error {image_response.status_code} while fetching Shopify image {image_id} details.")
                    st.text(image_response.text)  # Display response text for debugging
                    return None
            else:
                # If variant does not have a specific image, fall back to the product's default image
                if product_id:
                    product_image = get_shopify_default_product_image(product_id, store_prefix)
                    return product_image
                else:
                    return None
        else:
            st.error(f"HTTP Error {variant_response.status_code} while fetching Shopify variant {variant_id} details.")
            st.text(variant_response.text)  # Display response text for debugging
            return None
    except Exception as e:
        st.error(f"Exception occurred while fetching Shopify variant {variant_id} details: {e}")
        return None

# 🛍️ Function to get Shopify product's default image given a product ID and store prefix
def get_shopify_default_product_image(product_id, store_prefix):
    store = SHOPIFY_STORES.get(store_prefix.upper())
    if not store:
        st.error(f"No Shopify store configuration found for prefix '{store_prefix}'.")
        return None
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": store['access_token']
    }
    try:
        response = requests.get(f"https://{store['url']}/admin/api/2023-10/products/{product_id}.json", headers=headers)
        if response.status_code == 200:
            product = response.json().get("product", {})
            images = product.get("images", [])
            if images:
                return images[0].get("src")  # Return the first image as default
            else:
                return None
        else:
            st.error(f"HTTP Error {response.status_code} while fetching Shopify product {product_id} details.")
            st.text(response.text)  # Display response text for debugging
            return None
    except Exception as e:
        st.error(f"Exception occurred while fetching Shopify product {product_id} details: {e}")
        return None

# ==========================================
# 🎨 Streamlit App Layout and Logic
# ==========================================

# 🐟 App Title
st.set_page_config(page_title="🐟 Cat Kiss Fish & Shopify Order Comparator 🛍️", layout="wide")
st.title("🐟 Cat Kiss Fish & Shopify Order Comparator 🛍️")

# 📥 Multiple Order Input Instructions
st.sidebar.header("📥 Enter Multiple Order Numbers")

# 📥 Input Field in Sidebar for Multiple Orders
order_input = st.sidebar.text_area(
    "🔍 Enter Order Numbers",
    
)

# Parse the input into a list of (Cat Kiss Fish, Shopify) order pairs with store prefix
def parse_order_input(order_input_text):
    order_pairs = []
    lines = order_input_text.strip().split('\n')
    for idx, line in enumerate(lines, start=1):
        if line.strip():  # Ignore empty lines
            parts = line.strip().split()
            if len(parts) == 2:
                cat_order, shop_order = parts
                if len(shop_order) < 1:
                    st.sidebar.warning(f"Invalid Shopify order name in line {idx}: '{line}'.")
                    continue
                store_prefix = shop_order[0].upper()
                if store_prefix in SHOPIFY_STORES:
                    order_pairs.append((cat_order, shop_order, store_prefix))
                else:
                    st.sidebar.warning(f"Unknown store prefix '{store_prefix}' in line {idx}: '{line}'. Expected prefixes: {', '.join(SHOPIFY_STORES.keys())}.")
            else:
                st.sidebar.warning(f"Invalid format in line {idx}: '{line}'. Expected two order numbers separated by a space.")
    return order_pairs

order_pairs = parse_order_input(order_input)

# If there are order pairs, list them in the sidebar for selection
if order_pairs:
    st.sidebar.markdown("---")
    st.sidebar.header("🗂️ Select an Order to Compare")
    
    # Create a list of order identifiers for selection (e.g., "1: 2024091112121444123628 vs G61226 (Store G)")
    order_identifiers = [f"{idx+1}: {pair[0]} vs {pair[1]} (Store {pair[2]})" for idx, pair in enumerate(order_pairs)]
    
    # Display all orders using radio buttons
    selected_order_idx = st.sidebar.radio("🔽 Select an Order", options=range(len(order_pairs)), format_func=lambda x: order_identifiers[x])
    
    # Get the selected order pair
    selected_cat_order, selected_shop_order, selected_store_prefix = order_pairs[selected_order_idx]
    
    # Automatically trigger comparison upon selection
    # 🐟 Fetch Cat Kiss Fish Order Details
    with st.spinner(f"🔄 Fetching Cat Kiss Fish access token for Order {selected_cat_order}..."):
        catkissfish_token = get_catkissfish_access_token(CATKISSFISH_CLIENT_ID, CATKISSFISH_CLIENT_SECRET)
    
    if catkissfish_token:
        with st.spinner(f"📥 Fetching Cat Kiss Fish order details for Order {selected_cat_order}..."):
            catkissfish_order = get_catkissfish_order_details(selected_cat_order, catkissfish_token)
    else:
        st.error("❌ Unable to retrieve Cat Kiss Fish access token.")
        catkissfish_order = None
    
    # 🛍️ Fetch Shopify Order Details
    with st.spinner(f"📥 Fetching Shopify order details for Order {selected_shop_order} from Store '{selected_store_prefix}'..."):
        shopify_orders = get_shopify_order_details(selected_shop_order, selected_store_prefix)
    
    if not shopify_orders:
        shopify_order = None
    else:
        # Assuming order numbers are unique, take the first matched order
        shopify_order = shopify_orders[0]
    
    # 🖼️ Display the Results
    if catkissfish_order and shopify_order:
        st.success(f"✅ Both Order Details Retrieved Successfully!\n**Cat Kiss Fish Order:** {selected_cat_order}\n**Shopify Order:** {selected_shop_order} (Store '{selected_store_prefix}')")
        
        # 🐟 Cat Kiss Fish Order Details
        # Extracting required fields from orderDesignHistoryList
        order_design_history = catkissfish_order.get("orderDesignHistoryList", [])
        
        # Reverse the order of products
        order_design_history_reversed = order_design_history[::-1]
        
        # Initialize lists to store extracted data
        cat_product_names = []
        cat_size_names = []
        cat_quantities = []
        cat_effect_images = []
        
        for design in order_design_history_reversed:
            product_name = design.get("productName", "N/A")
            size_name = design.get("sizeName", "N/A")
            quantity = design.get("quantity", "N/A")
            effect_image_urls = design.get("effectImageUrl", "")
            urls = [url.strip() for url in effect_image_urls.split(",") if url.strip()]
            
            # Remove the last image
            if urls:
                urls = urls[:-1]
            
            cat_product_names.append(product_name)
            cat_size_names.append(size_name)
            cat_quantities.append(quantity)
            cat_effect_images.append(urls)
        
        # Aggregate the data for display
        catkissfish_data = {
            "Order ID": catkissfish_order.get("id", "N/A"),
            "Product Names": cat_product_names if cat_product_names else ["N/A"],
            "Size Names": cat_size_names if cat_size_names else ["N/A"],
            "Quantities": cat_quantities if cat_quantities else ["N/A"],
            "Customer Name": catkissfish_order.get("address", {}).get("userName", "N/A"),
            "Detail Address": catkissfish_order.get("address", {}).get("detailAddress", "N/A"),
            "Postal Code": catkissfish_order.get("address", {}).get("postalCode", "N/A"),
            # "Order Properties": cat_order_properties if cat_order_properties else []  # Removed as per request
        }
        
        # 🛍️ Shopify Order Details
        # Extracting order properties and product properties
        # shopify_order_properties = shopify_order.get("note_attributes", [])  # Removed Order Properties
        shopify_data = {
            "Order Number": shopify_order.get("order_number", "N/A"),
            "Product Names": [item.get("name", "N/A") for item in shopify_order.get("line_items", [])],
            "Size Names": [item.get("variant_title", "N/A") for item in shopify_order.get("line_items", [])],
            "Quantities": [str(item.get("quantity", "N/A")) for item in shopify_order.get("line_items", [])],
            "Customer Name": f"{shopify_order.get('customer', {}).get('first_name', '')} {shopify_order.get('customer', {}).get('last_name', '')}".strip(),
            "Detail Address": shopify_order.get("shipping_address", {}).get("address1", "N/A"),
            "Postal Code": shopify_order.get("shipping_address", {}).get("zip", "N/A"),
            # "Order Properties": shopify_order_properties,  # Removed Order Properties
            "Variant Images": []  # Placeholder for variant images
        }
        
        # 🛍️ Fetch Shopify Variant Images
        for item in shopify_order.get("line_items", []):
            variant_id = item.get("variant_id")
            if variant_id:
                image_url = get_shopify_variant_image(variant_id, selected_store_prefix)
                if image_url:
                    shopify_data["Variant Images"].append([image_url])  # List to maintain consistency
                else:
                    shopify_data["Variant Images"].append([])
            else:
                shopify_data["Variant Images"].append([])
        
        # 🗂️ Determine the number of products to align
        num_products_cat = len(catkissfish_data['Product Names'])
        num_products_shopify = len(shopify_data['Product Names'])
        max_products = max(num_products_cat, num_products_shopify)
        
        # Extend lists to match the maximum number of products
        while len(catkissfish_data['Product Names']) < max_products:
            catkissfish_data['Product Names'].append("N/A")
            catkissfish_data['Size Names'].append("N/A")
            cat_quantities.append("N/A")
            cat_effect_images.append([])
        
        while len(shopify_data['Product Names']) < max_products:
            shopify_data['Product Names'].append("N/A")
            shopify_data['Size Names'].append("N/A")
            shopify_data['Quantities'].append("N/A")
            shopify_data['Variant Images'].append([])
        
        # ==========================================
        # 📦 **Shipping Address Comparison**
        # ==========================================
        
        # Removed the heading "🏠 Shipping Address Comparison 🏠"
        col_addr1, col_addr2 = st.columns(2)
        
        with col_addr1:
            st.markdown("#### 🐟 **Cat Kiss Fish Shipping Address** 🐟")
            st.write(f"**Customer Name:** {catkissfish_data['Customer Name']}")
            st.write(f"**Detail Address:** {catkissfish_data['Detail Address']}")
            st.write(f"**Postal Code:** {catkissfish_data['Postal Code']}")
        
        with col_addr2:
            st.markdown("#### 🛍️ **Shopify Shipping Address** 🛍️")
            st.write(f"**Customer Name:** {shopify_data['Customer Name']}")
            st.write(f"**Detail Address:** {shopify_data['Detail Address']}")
            st.write(f"**Postal Code:** {shopify_data['Postal Code']}")
        
        st.markdown("---")
        
        # ==========================================
        # 📦 **Product Comparison**
        # ==========================================
        
        # Removed the heading "📦 Product Comparison 📦"
        st.markdown("### 📦 **Product Comparison** 📦")  # Retained for clarity
        
        for idx in range(max_products):
            st.markdown(f"#### 🛒 **Product {idx + 1} Comparison** 🛒")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"##### 🐟 **Cat Kiss Fish - Product {idx + 1}** 🐟")
                st.write(f"**Product Name:** {catkissfish_data['Product Names'][idx]}")
                st.write(f"**Size Name:** {catkissfish_data['Size Names'][idx]}")
                st.write(f"**Quantity:** {catkissfish_data['Quantities'][idx]}")
                
                # Display Effect Images in a Scrollable Square Box with height:700px; width:100%
                if cat_effect_images[idx]:
                    st.markdown("**Effect Images:**")
                    # Create a scrollable container using HTML and CSS with specified size
                    effect_images_html = f"""
                    <div style='height:700px; width:100%; overflow-y: scroll; border:1px solid #ccc; padding:5px;'>
                    """
                    for url in cat_effect_images[idx]:
                        effect_images_html += f"<img src='{url}' alt='Effect Image' style='width:100%; margin-bottom:10px;'>"
                    effect_images_html += "</div>"
                    st.markdown(effect_images_html, unsafe_allow_html=True)
                else:
                    st.write("**Effect Images:** No effect images available.")
            
            with col2:
                st.markdown(f"##### 🛍️ **Shopify - Product {idx + 1}** 🛍️")
                st.write(f"**Product Name:** {shopify_data['Product Names'][idx]}")
                
                # Display Product Properties Above Size Name and Remove "Product Properties:" Text
                line_item_properties = shopify_order["line_items"][idx].get("properties", []) if idx < num_products_shopify else []
                if line_item_properties:
                    for prop in line_item_properties:
                        key = prop.get("name", "N/A")
                        value = prop.get("value", "N/A")
                        st.write(f"- **{key}:** {value}")
                else:
                    st.write("- **No Product Properties Available.**")
                
                st.write(f"**Size Name:** {shopify_data['Size Names'][idx]}")
                st.write(f"**Quantity:** {shopify_data['Quantities'][idx]}")
                
                # Display Shopify Variant Image(s)
                variant_images = shopify_data['Variant Images'][idx]
                if variant_images:
                    st.markdown("**Product Variant Image:**")
                    for img_url in variant_images:
                        st.image(img_url, use_column_width=True)
                else:
                    st.write("**Product Variant Image:** No images available.")
            
            st.markdown("---")  # Separator between products
        
        # ==========================================
        # 📋 **Additional Order Information**
        # ==========================================
        
        st.markdown("---")
        st.markdown("### 📋 **Additional Order Information** 📋")
        additional_info_cols = st.columns(2)
        additional_info_cols[0].markdown(f"**Cat Kiss Fish Order ID:** {catkissfish_data.get('Order ID', 'N/A')}")
        additional_info_cols[1].markdown(f"**Shopify Order Number:** {shopify_data.get('Order Number', 'N/A')}")
    
    else:
        st.error("❌ Unable to retrieve one or both order details. Please check the order numbers and try again.")
else:
    # Removed the example and guide lines from the sidebar
    st.sidebar.warning("⚠️ Please enter at least one pair of order numbers to compare.")
