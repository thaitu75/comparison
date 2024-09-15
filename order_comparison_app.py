import streamlit as st
import requests
import json
import pandas as pd
import os
from dotenv import load_dotenv

# ==========================================
# 🔒 Configuration: Load Environment Variables
# ==========================================

# Load environment variables from .env file
load_dotenv()

# 🐟 Cat Kiss Fish API Credentials
CATKISSFISH_CLIENT_ID = os.getenv("CATKISSFISH_CLIENT_ID")
CATKISSFISH_CLIENT_SECRET = os.getenv("CATKISSFISH_CLIENT_SECRET")

# 🛍️ Shopify API Credentials
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")

# ==========================================
# 🌐 API Endpoints
# ==========================================

# 🐟 Cat Kiss Fish API Endpoints
CATKISSFISH_TOKEN_URL = "https://www.catkissfish.com:8443/oauth2/client_token"
CATKISSFISH_ORDER_DETAIL_URL = "https://www.catkissfish.com:8443/open/api/order/v1/order/detail"

# 🛍️ Shopify API Endpoint
SHOPIFY_API_BASE_URL = SHOPIFY_STORE_URL  # Using the provided Shopify store URL

# ==========================================
# 🚀 Functions to Interact with APIs
# ==========================================

# 🐟 Function to get access token from Cat Kiss Fish
@st.cache_data(ttl=7000)  # Cache the token for ~2 hours (7200 seconds)
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

# 🛍️ Function to get order details from Shopify
def get_shopify_order_details(order_number):
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
    }
    params = {
        "name": order_number
    }
    try:
        response = requests.get(SHOPIFY_API_BASE_URL, headers=headers, params=params)
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

# ==========================================
# 🎨 Streamlit App Layout and Logic
# ==========================================

# 🐟 App Title
st.set_page_config(page_title="🐟 Cat Kiss Fish & Shopify Order Comparator 🛍️", layout="wide")
st.title("🐟 Cat Kiss Fish & Shopify Order Comparator 🛍️")

# 📥 Multiple Order Input Instructions
st.sidebar.header("📥 Enter Multiple Order Numbers")
st.sidebar.markdown("""
Enter multiple **Cat Kiss Fish Order Numbers** and **Shopify Order Numbers** below.  
Each line should contain a pair separated by a space.

**Example:**
""")

# 📥 Input Field in Sidebar for Multiple Orders
order_input = st.sidebar.text_area("🔍 Enter Order Numbers", "2024091112121444123628 G61226\n2024091110490123363860 G61227\n2024091110540123144343 G61228")

# Parse the input into a list of (Cat Kiss Fish, Shopify) order pairs
def parse_order_input(order_input_text):
    order_pairs = []
    lines = order_input_text.strip().split('\n')
    for line in lines:
        if line.strip():  # Ignore empty lines
            parts = line.strip().split()
            if len(parts) == 2:
                cat_order, shop_order = parts
                order_pairs.append((cat_order, shop_order))
            else:
                st.sidebar.warning(f"Invalid format in line: '{line}'. Expected two order numbers separated by a space.")
    return order_pairs

order_pairs = parse_order_input(order_input)

# If there are order pairs, list them in the sidebar for selection
if order_pairs:
    st.sidebar.markdown("---")
    st.sidebar.header("🗂️ Select an Order to Compare")
    
    # Create a list of order identifiers for selection (e.g., "1: 2024091112121444123628 vs G61226")
    order_identifiers = [f"{idx+1}: {pair[0]} vs {pair[1]}" for idx, pair in enumerate(order_pairs)]
    
    # Display all orders using radio buttons
    selected_order_idx = st.sidebar.radio("🔽 Select an Order", options=range(len(order_pairs)), format_func=lambda x: order_identifiers[x])
    
    # Get the selected order pair
    selected_cat_order, selected_shop_order = order_pairs[selected_order_idx]
    
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
    with st.spinner(f"📥 Fetching Shopify order details for Order {selected_shop_order}..."):
        shopify_orders = get_shopify_order_details(selected_shop_order)
    
    if not shopify_orders:
        shopify_order = None
    else:
        # Assuming order numbers are unique, take the first matched order
        shopify_order = shopify_orders[0]
    
    # 🖼️ Display the Results
    if catkissfish_order and shopify_order:
        st.success(f"✅ Both Order Details Retrieved Successfully!\n**Cat Kiss Fish Order:** {selected_cat_order}\n**Shopify Order:** {selected_shop_order}")
        
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
        cat_order_properties = catkissfish_order.get("orderProperties", [])  # Assuming orderProperties exists
        
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
            "Order Properties": cat_order_properties if cat_order_properties else []
        }
        
        # 🛍️ Shopify Order Details
        # Extracting order properties and product properties
        shopify_order_properties = shopify_order.get("note_attributes", [])  # Order properties in Shopify are usually in note_attributes
        shopify_data = {
            "Order Number": shopify_order.get("order_number", "N/A"),
            "Product Names": [item.get("name", "N/A") for item in shopify_order.get("line_items", [])],
            "Size Names": [item.get("variant_title", "N/A") for item in shopify_order.get("line_items", [])],
            "Quantities": [str(item.get("quantity", "N/A")) for item in shopify_order.get("line_items", [])],
            "Customer Name": f"{shopify_order.get('customer', {}).get('first_name', '')} {shopify_order.get('customer', {}).get('last_name', '')}".strip(),
            "Detail Address": shopify_order.get("shipping_address", {}).get("address1", "N/A"),
            "Postal Code": shopify_order.get("shipping_address", {}).get("zip", "N/A"),
            "Order Properties": shopify_order_properties
        }
        
        # 🗂️ Determine the number of products to align
        num_products_cat = len(catkissfish_data['Product Names'])
        num_products_shopify = len(shopify_data['Product Names'])
        max_products = max(num_products_cat, num_products_shopify)
        
        # Extend lists to match the maximum number of products
        while len(catkissfish_data['Product Names']) < max_products:
            catkissfish_data['Product Names'].append("N/A")
            catkissfish_data['Size Names'].append("N/A")
            catkissfish_data['Quantities'].append("N/A")
            cat_effect_images.append([])
        
        while len(shopify_data['Product Names']) < max_products:
            shopify_data['Product Names'].append("N/A")
            shopify_data['Size Names'].append("N/A")
            shopify_data['Quantities'].append("N/A")
        
        # ==========================================
        # 📦 **Shipping Address Comparison**
        # ==========================================
        
        st.markdown("### 🏠 **Shipping Address Comparison** 🏠")
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
        
        st.markdown("### 📦 **Product Comparison** 📦")
        
        for idx in range(max_products):
            st.markdown(f"#### 🛒 **Product {idx + 1} Comparison** 🛒")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"##### 🐟 **Cat Kiss Fish - Product {idx + 1}** 🐟")
                st.write(f"**Product Name:** {catkissfish_data['Product Names'][idx]}")
                st.write(f"**Size Name:** {catkissfish_data['Size Names'][idx]}")
                st.write(f"**Quantity:** {catkissfish_data['Quantities'][idx]}")
                
                # Display Effect Images in a Scrollable Square Box
                if cat_effect_images[idx]:
                    st.markdown("**Effect Images:**")
                    # Create a scrollable container using HTML and CSS
                    effect_images_html = f"""
                    <div style='height:800px; width:100%; overflow-y: scroll; border:1px solid #ccc; padding:5px;'>
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
            
            st.markdown("---")  # Separator between products
        
        # ==========================================
        # 🐟 **Cat Kiss Fish Order Properties**
        # ==========================================
        
        if catkissfish_data["Order Properties"]:
            st.markdown("### 🐟 **Cat Kiss Fish Order Properties** 🐟")
            for prop in catkissfish_data["Order Properties"]:
                key = prop.get("key", "N/A")
                value = prop.get("value", "N/A")
                st.write(f"- **{key}:** {value}")
        else:
            st.write("### 🐟 **Cat Kiss Fish Order Properties** 🐟")
            st.write("No order properties available.")
        
        # ==========================================
        # 🛍️ **Shopify Order Properties**
        # ==========================================
        
        if shopify_data["Order Properties"]:
            st.markdown("### 🛍️ **Shopify Order Properties** 🛍️")
            for prop in shopify_data["Order Properties"]:
                key = prop.get("name", "N/A")
                value = prop.get("value", "N/A")
                st.write(f"- **{key}:** {value}")
        else:
            st.write("### 🛍️ **Shopify Order Properties** 🛍️")
            st.write("No order properties available.")
        
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
    st.sidebar.warning("⚠️ Please enter at least one pair of order numbers to compare.")
