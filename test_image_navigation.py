import streamlit as st

# Initialize session state for image indices if not already done
if 'image_indices' not in st.session_state:
    st.session_state['image_indices'] = {}

# Sample data for multiple products
products = [
    {
        "name": "Product A",
        "size": "Large",
        "quantity": 2,
        "images": [
            "https://via.placeholder.com/400x300.png?text=Product+A+Image+1",
            "https://via.placeholder.com/400x300.png?text=Product+A+Image+2"
        ]
    },
    {
        "name": "Product B",
        "size": "Medium",
        "quantity": 1,
        "images": [
            "https://via.placeholder.com/400x300.png?text=Product+B+Image+1",
            "https://via.placeholder.com/400x300.png?text=Product+B+Image+2",
            "https://via.placeholder.com/400x300.png?text=Product+B+Image+3"
        ]
    }
]

# Iterate over each product
for idx, product in enumerate(products, start=1):
    st.markdown(f"### **{product['name']}**")
    st.write(f"**Size:** {product['size']}")
    st.write(f"**Quantity:** {product['quantity']}")

    image_urls = product['images']
    image_labels = [f"Image {i+1}" for i in range(len(image_urls))]

    # Unique key for each product's selectbox
    selectbox_key = f"selectbox_{idx}"

    # Initialize image index for the product
    if selectbox_key not in st.session_state['image_indices']:
        st.session_state['image_indices'][selectbox_key] = 0

    # Selectbox for image selection
    selected_image = st.selectbox(
        f"Select an Image for {product['name']}",
        options=image_labels,
        index=st.session_state['image_indices'][selectbox_key],
        key=selectbox_key
    )

    # Update the current image index based on selection
    st.session_state['image_indices'][selectbox_key] = image_labels.index(selected_image)

    # Display the selected image
    st.image(
        image_urls[st.session_state['image_indices'][selectbox_key]],
        caption=selected_image,
        use_column_width=True
    )

    # Debug Statement
    st.write(f"**Debug:** {product['name']} - Current Image Index: {st.session_state['image_indices'][selectbox_key]}")
    st.markdown("---")  # Separator between products
