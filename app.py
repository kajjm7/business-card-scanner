import streamlit as st
import requests
import base64
import json
import os
import pandas as pd

def encode_image(image_bytes):
    """Convert image bytes to a base64 string."""
    return base64.b64encode(image_bytes).decode('utf-8')

# Initialize session state to hold scanned cards in memory
if "scanned_cards" not in st.session_state:
    st.session_state.scanned_cards = []

st.set_page_config(page_title="Business Card Scanner", page_icon="📇")
st.title("📇 Business Card Scanner")
st.write("Capture or upload a business card to extract details using your Llama Vision model.")

capture_method = st.radio("Choose input method:", ["Camera", "File Upload"])

img_file = None
if capture_method == "Camera":
    img_file = st.camera_input("Position the business card and take a picture")
else:
    img_file = st.file_uploader("Upload a business card image", type=["jpg", "jpeg", "png"])

if img_file is not None:
    st.image(img_file, caption="Card to process", use_container_width=True)

    if st.button("Extract Information", type="primary"):
        with st.spinner("Analyzing with Llama Vision..."):
            
            base64_image = encode_image(img_file.getvalue())

            # Use Render environment variables and forcefully strip hidden characters or quotes
            raw_url = os.getenv("REMOTE_API_URL", "https://chat.758453567.xyz/api/chat/completions")
            REMOTE_API_URL = "https://chat.758453567.xyz/api/chat/completions"
            API_KEY = os.getenv("OPEN_WEBUI_API_KEY", "")
            MODEL_NAME = os.getenv("MODEL_NAME", "forced-gpu-llama:latest")

            prompt = """
            You are an AI business card scanner. Extract the details from the provided business card image.
            Output strictly a valid JSON object with the following keys:
            "Name", "Title", "Company", "Email", "Phone", "Website", "Address".
            If a field is not present on the card, set its value to null.
            Do not output any markdown formatting, backticks, or conversational text. Output ONLY the raw JSON object.
            """

            # Configure headers with a browser User-Agent to bypass Cloudflare Bot Protection
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                "stream": False
            }

            # Send API request with robust error handling
            try:
                response = requests.post(REMOTE_API_URL, headers=headers, json=payload, timeout=45)
                
                # Grab the raw text FIRST before trying to parse it as JSON
                raw_text = response.text
                
                # Check for 404 or 500 HTTP errors
                response.raise_for_status()
                
                # Parse OpenAI response format
                result = json.loads(raw_text)
                llm_text = result["choices"][0]["message"]["content"]
                
                # Clean up any surrounding markdown blocks (e.g. ```json ... ```)
                cleaned_text = llm_text.replace("```json", "").replace("```", "").strip()
                extracted_data = json.loads(cleaned_text)
                
                # Add the new data to our running list
                st.session_state.scanned_cards.append(extracted_data)
                st.success("Extraction Complete! Added to your list below.")

            except requests.exceptions.RequestException as e:
                st.error(f"Network error: {e}")
                # This will print the exact HTML Cloudflare or the server rejected us with
                if 'raw_text' in locals() and raw_text:
                    st.error("The server returned this instead of JSON (Check for Cloudflare Captcha or 404 page):")
                    st.code(raw_text[:500]) 
                    
            except json.JSONDecodeError:
                st.error("The server did not return valid JSON. Here is the raw response:")
                if 'raw_text' in locals():
                    st.code(raw_text[:500])

# --- CSV EXPORT SECTION ---
st.divider()
st.subheader("📁 Scanned Contacts (Current Session)")

if st.session_state.scanned_cards:
    # Convert the list of dictionaries into a Pandas DataFrame
    df = pd.DataFrame(st.session_state.scanned_cards)
    
    # Display the table on the webpage
    st.dataframe(df, use_container_width=True)
    
    # Convert the DataFrame to a CSV string
    csv_data = df.to_csv(index=False).encode('utf-8')
    
    # Create the download button
    st.download_button(
        label="📥 Download all as CSV",
        data=csv_data,
        file_name="scanned_business_cards.csv",
        mime="text/csv",
        type="primary"
    )
else:
    st.info("No cards scanned yet. Your extracted contacts will appear here.")