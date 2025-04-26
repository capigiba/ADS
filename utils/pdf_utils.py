import os, base64, urllib.request
import streamlit as st
from streamlit.components.v1 import html

def show_pdf(path_or_url: str, width: int = 700, height: int = 800):
    """
    Embed a PDF (local file or remote URL) into Streamlit via a base64-encoded data URI.
    Avoids Chrome’s SAMEORIGIN / file:// blocking when you would otherwise use an <iframe>.
    """
    try:
        if path_or_url.lower().startswith(("http://", "https://")):
            with urllib.request.urlopen(path_or_url) as resp:
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

    # Base64-encode and build the <iframe>
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_iframe = f"""
    <iframe
      src="data:application/pdf;base64,{b64}"
      width="{width}"
      height="{height}"
      style="border: none;"
      type="application/pdf">
    </iframe>
    """

    # Render via the HTML component (no extra wrapping/sanitization)
    html(pdf_iframe, width=width, height=height)