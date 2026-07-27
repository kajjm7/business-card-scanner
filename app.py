import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
import pandas as pd

def create_vcard_bundle(contacts):
    """Converts a list of contact dictionaries into a single combined .vcf file string."""
    vcards = []
    for c in contacts:
        first = c.get('First Name') or ''
        last = c.get('Last Name') or ''
        
        vcard_lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"N:{last};{first};;;",
            f"FN:{first} {last}".strip(),
            f"ORG:{c.get('Company') or ''}",
            f"TITLE:{c.get('Title') or ''}",
            f"EMAIL;TYPE=INTERNET:{c.get('Email') or ''}",
            f"TEL;TYPE=WORK,VOICE:{c.get('Office Phone') or ''}",
            f"TEL;TYPE=CELL,VOICE:{c.get('Mobile Phone') or ''}",
            f"URL:{c.get('Website') or ''}",
            f"ADR;TYPE=WORK:;;{c.get('Street Address') or ''};{c.get('City') or ''};{c.get('State') or ''};{c.get('Zip') or ''};",
            "END:VCARD"
        ]
        vcards.append("\n".join(vcard_lines))
        
    return "\n\n".join(vcards)

# --- (Rest of your app setup and Gemini extraction code remains the same) ---

# Initialize session state to hold scanned cards in memory
if "scanned_cards" not in st.session_state:
    st.session_state.scanned_cards = []

st.set_page_config(page_title="Business Card Scanner", page_icon="📇")
st.title("📇 Business Card Scanner")
st.write("Capture or upload business cards to extract details using Google Gemini.")

capture_method = st.radio("Choose input method:", ["Camera", "File Upload"])

images_to_process = []

if capture_method == "Camera":
    img_file = st.camera_input("Position the business card and take a picture")
    if img_file is not None:
        images_to_process.append(img_file)
        st.image(img_file, caption="Card to process", use_container_width=True)
else:
    uploaded_files = st.file_uploader(
        "Upload business card images", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )
    if uploaded_files:
        images_to_process.extend(uploaded_files)
        st.write(f"📁 **{len(uploaded_files)} image(s) queued for processing.**")

if images_to_process:
    if st.button("Extract Information", type="primary"):
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        if not GOOGLE_API_KEY:
            st.error("Missing Google API Key. Please add it to your environment variables.")
            st.stop()
            
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-3.6-flash')
            
            prompt = """
            You are an AI business card scanner. Extract the details from the provided business card image.
            Output strictly a valid JSON object with the following exact keys:
            "First Name", "Last Name", "Title", "Company", "Email", "Office Phone", "Mobile Phone", "Website", "Street Address", "City", "State", "Zip".
            If a field is not present on the card, set its value to null. 
            Do not combine fields.
            """
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for index, file in enumerate(images_to_process):
                status_text.text(f"Processing card {index + 1} of {len(images_to_process)}...")
                
                img = Image.open(file)
                response = model.generate_content(
                    [prompt, img],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                extracted_data = json.loads(response.text)
                st.session_state.scanned_cards.append(extracted_data)
                
                progress_bar.progress((index + 1) / len(images_to_process))
            
            status_text.success(f"Successfully extracted {len(images_to_process)} card(s)! Added to your list below.")

        except Exception as e:
            st.error(f"An error occurred during extraction: {e}")

# --- EXPORT SECTION ---
st.divider()
st.subheader("📁 Scanned Contacts (Current Session)")

if st.session_state.scanned_cards:
    df = pd.DataFrame(st.session_state.scanned_cards)
    
    # Interactive data table for typo corrections
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
    current_contacts = edited_df.to_dict('records')
    st.session_state.scanned_cards = current_contacts
    
    col1, col2 = st.columns(2)
    
    # 1. Download CSV
    with col1:
        csv_data = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download all as CSV",
            data=csv_data,
            file_name="scanned_business_cards.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # 2. Download vCard (.vcf) for Outlook / Mobile
    with col2:
        vcard_data = create_vcard_bundle(current_contacts)
        st.download_button(
            label="📇 Export for Outlook (.vcf)",
            data=vcard_data,
            file_name="contacts_for_outlook.vcf",
            mime="text/vcard",
            type="primary",
            use_container_width=True
        )
else:
    st.info("No cards scanned yet. Your extracted contacts will appear here.")