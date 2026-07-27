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
st.write("Capture or upload a business card to extract details using Google Gemini.")

capture_method = st.radio("Choose input method:", ["Camera", "File Upload"])

img_file = None
if capture_method == "Camera":
    img_file = st.camera_input("Position the business card and take a picture")
else:
    img_file = st.file_uploader("Upload a business card image", type=["jpg", "jpeg", "png"])

if img_file is not None:
    st.image(img_file, caption="Card to process", use_container_width=True)

    if st.button("Extract Information", type="primary"):
        with st.spinner("Analyzing with Gemini..."):
            try:
                # 1. Fetch the API Key
                GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
                if not GOOGLE_API_KEY:
                    st.error("Missing Google API Key. Please add it to your environment variables.")
                    st.stop()
                
                # 2. Configure the Gemini API
                genai.configure(api_key=GOOGLE_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 3. Format the image using Pillow (required by the Google library)
                img = Image.open(img_file)
                
                # 4. Define the prompt
                prompt = """
                You are an AI business card scanner. Extract the details from the provided business card image.
                Output strictly a valid JSON object with the following keys:
                "Name", "Title", "Company", "Email", "Phone", "Website", "Address".
                If a field is not present on the card, set its value to null.
                """
                
                # 5. Send to Gemini, forcing a strict JSON output
                response = model.generate_content(
                    [prompt, img],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                # 6. Parse the response and save it
                extracted_data = json.loads(response.text)
                st.session_state.scanned_cards.append(extracted_data)
                st.success("Extraction Complete! Added to your list below.")

            except Exception as e:
                st.error(f"An error occurred during extraction: {e}")

# --- CSV EXPORT SECTION ---
st.divider()
st.subheader("📁 Scanned Contacts (Current Session)")

if st.session_state.scanned_cards:
    df = pd.DataFrame(st.session_state.scanned_cards)
    st.dataframe(df, use_container_width=True)
    
    csv_data = df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Download all as CSV",
        data=csv_data,
        file_name="scanned_business_cards.csv",
        mime="text/csv",
        type="primary"
    )
else:
    st.info("No cards scanned yet. Your extracted contacts will appear here.")