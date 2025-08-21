import streamlit as st
import zipfile, io
from BatchPdfConv import BatchPdfConv  

from dotenv import load_dotenv
load_dotenv()

# --- CONFIGURATION UI ---
st.sidebar.title("⚙️ Configuration")
api_key = st.sidebar.text_input("Mistral API Key", type="password")

# Uploader (1 ou plusieurs fichiers)
st.sidebar.subheader("📂 Upload files")
single_file = st.sidebar.file_uploader("Single file", type="pdf", key="single")
multi_files = st.sidebar.file_uploader("Multiple files", type="pdf", accept_multiple_files=True, key="multi")

# --- MAIN CONTENT ---
st.title("Mistral OCR - PDF to Markdown")

uploaded_files = []
if single_file:
    uploaded_files.append(single_file)
if multi_files:
    uploaded_files.extend(multi_files)

# Affichage liste des fichiers uploadés
if uploaded_files:
    st.subheader("📑 Fichiers à traiter")
    for f in uploaded_files:
        st.text(f.name)

# --- Conversion ---
if st.button("Convert ..." ) and uploaded_files:
    if not api_key:
        st.error("⚠️ Please enter your Mistral API Key in the sidebar.")
    else:
        converter = BatchPdfConv(api_key=api_key)
        results = {}

        with st.spinner("Traitement et conversion..."):
            for f in uploaded_files:
                try:
                    md = converter.convert_pdf_to_markdown(f.name)
                    results[f.name] = md
                except Exception as e:
                    st.error(f"❌ {f.name}: {e}")

        if results:
            st.success("✅ Conversion terminée !")

            # Téléchargement fichiers individuels
            st.subheader("⬇️ Téléchargement des résultats")
            for name, content in results.items():
                st.download_button(
                    f"Télécharger {name}.md",
                    data=content,
                    file_name=name.replace(".pdf", ".md"),
                    mime="text/markdown"
                )

            # Téléchargement en ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for name, content in results.items():
                    zipf.writestr(name.replace(".pdf", ".md"), content)
            zip_buffer.seek(0)

            st.download_button(
                "📦 Télécharger en archive ZIP",
                data=zip_buffer,
                file_name="results.zip",
                mime="application/zip"
            )
