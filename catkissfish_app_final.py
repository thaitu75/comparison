import streamlit as st
import requests
import json

# Configuration - Replace these with your actual client_id and client_secret
CLIENT_ID = "4HN3BTXHKJZ3SBTG"
CLIENT_SECRET = "7ios5rskcetqx3c5h2yjokc3jvgxut0m"

# API Endpoints
TOKEN_URL = "https://www.catkissfish.com:8443/oauth2/client_token"
ORDER_DETAIL_URL = "https://www.catkissfish.com:8443/open/api/order/v1/order/detail"

# Function to get access token
@st.cache_data(ttl=7000)  # Cache the token for ~2 hours (7200 seconds)
def get_access_token(client_id, client_secret):
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    try:
        response = requests.post(TOKEN_URL, data=payload)
        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get("code") in [200, 0]:
                return resp_json["data"]["client_token"]
            else:
                st.error(f"Error obtaining token: {resp_json.get('msg')}")
                st.json(resp_json)  # Display full response for debugging
                return None
        else:
            st.error(f"HTTP Error {response.status_code} while obtaining token.")
            st.text(response.text)  # Display response text for debugging
            return None
    except Exception as e:
        st.error(f"Exception occurred while obtaining token: {e}")
        return None

# Function to get order details
def get_order_details(order_id, access_token):
    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "access_token": access_token
    }
    params = {
        "id": order_id
    }
    try:
        response = requests.get(ORDER_DETAIL_URL, headers=headers, params=params)
        if response.status_code == 200:
            resp_json = response.json()
            # Adjusting to accept code 0 as success based on the provided response
            if resp_json.get("code") in [200, 0]:
                return resp_json["data"]
            else:
                st.error(f"API Error: {resp_json.get('message')}")
                st.json(resp_json)  # Display full response for debugging
                return None
        else:
            st.error(f"HTTP Error {response.status_code} while fetching order details.")
            st.text(response.text)  # Display response text for debugging
            return None
    except Exception as e:
        st.error(f"Exception occurred while fetching order details: {e}")
        return None

# Streamlit App Layout
st.set_page_config(page_title="🐟 Cat Kiss Fish Order Details Viewer 🐟", layout="wide")
st.title("🐟 Cat Kiss Fish Order Details Viewer 🐟")
st.markdown("""
Enter your **Cat Kiss Fish Order Number** below to retrieve detailed information about your order.
""")

# Input field for Order ID
order_id = st.text_input("🔍 Enter Order Number", "2024091012145510038011")

# Button to fetch order details
if st.button("📥 Get Order Details"):
    if not order_id.strip():
        st.warning("⚠️ Please enter a valid Order Number.")
    else:
        with st.spinner("🔄 Fetching access token..."):
            token = get_access_token(CLIENT_ID, CLIENT_SECRET)
        
        if token:
            with st.spinner("📥 Fetching order details..."):
                order_data = get_order_details(order_id, token)
            
            if order_data:
                st.success("✅ Order Details Retrieved Successfully!")
                
                # Displaying the Address Details
                address = order_data.get("address", {})
                user_name = address.get("userName", "N/A")
                detail_address = address.get("detailAddress", "N/A")
                postal_code = address.get("postalCode", "N/A")
                country = address.get("country", "N/A")
                province = address.get("province", "N/A")
                city = address.get("city", "N/A")
                
                st.markdown("### 🏠 **Shipping Address** 🏠")
                address_cols = st.columns(3)
                address_cols[0].markdown(f"**User Name:** {user_name}")
                address_cols[1].markdown(f"**Detail Address:** {detail_address}")
                address_cols[2].markdown(f"**Postal Code:** {postal_code}")
                
                # Displaying Order Design History List
                order_design_history = order_data.get("orderDesignHistoryList", [])
                
                if order_design_history:
                    st.markdown("### 🎨 **Order Design Details** 🎨")
                    
                    for idx, design in enumerate(order_design_history, start=1):
                        st.markdown(f"#### 🖼️ **Design {idx}** 🖼️")
                        design_cols = st.columns(2)
                        
                        # Extracting fields
                        product_name = design.get("productName", "N/A")
                        size_name = design.get("sizeName", "N/A")
                        quantity = design.get("quantity", "N/A")
                        effect_image_urls = design.get("effectImageUrl", "")
                        
                        # Displaying Product Name, Size, Quantity
                        with design_cols[0]:
                            st.write(f"**Product Name:** {product_name}")
                            st.write(f"**Size Name:** {size_name}")
                            st.write(f"**Quantity:** {quantity}")
                        
                        # Displaying Effect Images
                        with design_cols[1]:
                            if effect_image_urls:
                                urls = [url.strip() for url in effect_image_urls.split(",") if url.strip()]
                                for url in urls:
                                    st.image(url, caption="Effect Image", use_column_width=True)
                            else:
                                st.write("No effect images available.")
                        
                        st.markdown("---")  # Separator between designs
                else:
                    st.write("No design history available for this order.")
                
                # Optional: Display Additional Order Information
                st.markdown("### 📋 **Additional Order Information** 📋")
                additional_info_cols = st.columns(2)
                additional_info_cols[0].markdown(f"**Order ID:** {order_data.get('id', 'N/A')}")
                additional_info_cols[1].markdown(f"**Total Amount:** {order_data.get('amount', 'N/A')}")
        else:
            st.error("Failed to retrieve access token. Please check your API credentials and try again.")
