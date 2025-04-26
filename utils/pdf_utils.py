import os, base64, urllib.request
import streamlit as st

def show_pdf(path_or_url: str, width='100%', height='800'):
    """Embed a PDF from a URL or local path into an iframe."""
    try:
        if path_or_url.lower().startswith(("http://", "https://")):
            resp = urllib.request.urlopen(path_or_url)
            pdf_bytes = resp.read()
        else:
            abs_path = os.path.abspath(path_or_url)
            if not os.path.exists(abs_path):
                st.error(f"❌ PDF not found at: {abs_path}")
                return
            with open(abs_path, "rb") as f:
                pdf_bytes = f.read()
    except Exception as e:
        st.error(f"❌ Could not load PDF:\n{e}")
        return

    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    iframe = f'''
    <iframe src="data:application/pdf;base64,{b64}"
            width="{width}" height="{height}" style="border:none;"></iframe>
    '''
    st.markdown(iframe, unsafe_allow_html=True)
