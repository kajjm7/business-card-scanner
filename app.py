import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
import pandas as pd

# Initialize session state to hold scanned cards in memory
if "scanned_cards" not in st.session_state:
    st.session_state.scanned_cards = []

st.set_page_config(page_title="Business Card Scanner", page_icon="📇")
st.title("📇 Business Card Scanner")
st.write("Capture or upload business cards to extract details using Google Gemini.")

capture_method = st.radio("Choose input method:", ["Camera", "File Upload"])

# Create a single list to hold whatever images the user provides
images_to_process = []

if capture_method == "Camera":
    img_file = st.camera_input("Position the business card and take a picture")
    if img_file is not None:
        images_to_process.append(img_file)
        st.image(img_file, caption="Card to process", use_container_width=True)
else:
    # 1. Enable multiple file uploads
    uploaded_files = st.file_uploader(
        "Upload business card images", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )
    if uploaded_files:
        images_to_process.extend(uploaded_files)
        st.write(f"📁 **{len(uploaded_files)} image(s) queued for processing.**")

# Only show the extract button if we have at least one image
if images_to_process:
    if st.button("Extract Information", type="primary"):
        
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        if not GOOGLE_API_KEY:
            st.error("Missing Google API Key. Please add it to your environment variables.")
            st.stop()
            
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = """
            You are an AI business card scanner. Extract the details from the provided business card image.
            Output strictly a valid JSON object with the following keys:
            "Name", "Title", "Company", "Email", "Phone", "Website", "Address".
            If a field is not present on the card, set its value to null.
            """
            
            # 2. Set up the progress bar UI
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 3. Loop through every image provided
            for index, file in enumerate(images_to_process):
                status_text.text(f"Processing card {index + 1} of {len(images_to_process)}...")
                
                img = Image.open(file)
                response = model.generate_content(
                    [prompt, img],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                extracted_data = json.loads(response.text)
                st.session_state.scanned_cards.append(extracted_data)
                
                # Update the progress bar mathematically
                progress_bar.progress((index + 1) / len(images_to_process))
            
            status_text.success(f"Successfully extracted {len(images_to_process)} card(s)! Added to your list below.")

        except Exception as e:
            st.error(f"An error occurred during extraction: {e}")

# --- CSV EXPORT SECTION ---
st.divider()
st.subheader("📁 Scanned Contacts (Current Session)")

if st.session_state.scanned_cards:
    df = pd.DataFrame(st.session_state.scanned_cards)
    
    # Interactive data table for typo corrections
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
    st.session_state.scanned_cards = edited_df.to_dict('records')
    
    csv_data = edited_df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Download all as CSV",
        data=csv_data,
        file_name="scanned_business_cards.csv",
        mime="text/csv",
        type="primary"
    )
else:
    st.info("No cards scanned yet. Your extracted contacts will appear here.")