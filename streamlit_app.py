import os
import base64
import logging
import streamlit as st
from dotenv import load_dotenv
from mistralai import Mistral

# Load environment variables
load_dotenv()


def ensure_output_dirs():
    os.makedirs("output/markdown", exist_ok=True)
    os.makedirs("output/logs", exist_ok=True)
    os.makedirs("output/processed", exist_ok=True)

def save_markdown(pdf_filename, markdown_text):
    base_name = os.path.splitext(pdf_filename)[0]
    output_path = f"output/markdown/{base_name}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)
    return output_path


# Config
API_KEY = os.getenv("MISTRAL_API_KEY")
if not API_KEY:
    st.error("⚠️ API key MISTRAL_API_KEY not found in .env file.")
    st.stop()

# Init client
client = Mistral(api_key=API_KEY)

# Setup logging
logging.basicConfig(
    filename="output/logs/conversion.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# UI
st.set_page_config(page_title="Mistral OCR", layout="wide")
st.title("📄 Mistral OCR - PDF to Markdown")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    st.write(f"**File uploaded:** {uploaded_file.name}")
    
    # Read PDF as base64
    try:
        b64_pdf = base64.b64encode(uploaded_file.read()).decode("utf-8")
    except Exception as e:
        st.error(f"Failed to encode file: {e}")
        st.stop()
    
    if st.button("🚀 Convert to Markdown"):
        with st.spinner("Processing with Mistral OCR..."):
            try:
                ensure_output_dirs()
                response = client.ocr.process(
                    model="mistral-ocr-latest",
                    document={
                        "type": "document_url",
                        "document_url": f"data:application/pdf;base64,{b64_pdf}"
                    },
                    include_image_base64=False
                )

                markdown_content = ""
                for page in response.pages:
                    markdown_content += f"## Page {page.index + 1}\n\n{page.markdown}\n\n"

                # Save markdown file
                output_path = save_markdown(uploaded_file.name, markdown_content)

                st.success(f"✅ Conversion completed! Saved at `{output_path}`")
                st.download_button(
                    "⬇️ Download Markdown",
                    data=markdown_content,
                    file_name=output_path.split("/")[-1],
                    mime="text/markdown"
                )

            except Exception as e:
                logging.error(f"Error processing file: {e}")
                st.error(f"❌ Error: {e}")
