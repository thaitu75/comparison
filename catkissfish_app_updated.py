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
            if resp_json.get("code") == 200 or resp_json.get("code") == 0:
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
            if resp_json.get("code") == 200 or resp_json.get("code") == 0:
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
st.title("Cat Kiss Fish Order Details Viewer")
st.write("Enter your Cat Kiss Fish Order Number below to retrieve order details.")

# Input field for Order ID
order_id = st.text_input("Enter Order Number", "2024091012145510038011")

# Button to fetch order details
if st.button("Get Order Details"):
    if not order_id:
        st.warning("Please enter a valid Order Number.")
    else:
        with st.spinner("Fetching access token..."):
            token = get_access_token(CLIENT_ID, CLIENT_SECRET)
        
        if token:
            with st.spinner("Fetching order details..."):
                order_data = get_order_details(order_id, token)
            
            if order_data:
                st.success("Order Details Retrieved Successfully!")
                
                # Displaying the desired fields
                
                # 1. Size Name
                size_name = order_data.get("sizeName", "N/A")
                st.write(f"**Size Name:** {size_name}")
                
                # 2. Quantity
                quantity = order_data.get("quantity", "N/A")
                st.write(f"**Quantity:** {quantity}")
                
                # 3. Product Name
                product_name = order_data.get("productName", "N/A")
                st.write(f"**Product Name:** {product_name}")
                
                # 4. Address Details
                address = order_data.get("address", {})
                user_name = address.get("userName", "N/A")
                detail_address = address.get("detailAddress", "N/A")
                postal_code = address.get("postalCode", "N/A")
                
                st.write("**Address Details:**")
                st.write(f"  - **User Name:** {user_name}")
                st.write(f"  - **Detail Address:** {detail_address}")
                st.write(f"  - **Postal Code:** {postal_code}")
                
                # 5. Order Design History List - Effect Image URLs
                order_design_history = order_data.get("orderDesignHistoryList", [])
                
                if order_design_history:
                    st.write("**Effect Images:**")
                    for idx, design in enumerate(order_design_history, start=1):
                        effect_urls = design.get("effectImageUrl", "")
                        # Split the comma-separated URLs
                        urls = [url.strip() for url in effect_urls.split(",") if url.strip()]
                        st.write(f"**Design {idx}:**")
                        for url in urls:
                            st.image(url, caption=f"Effect Image {idx}", use_column_width=True)
                else:
                    st.write("**Effect Images:** No effect images found.")
                
                # Optional: Display additional information or fields as needed
