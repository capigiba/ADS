import streamlit as st
import uuid
from typing import List, Optional

def reset_page_state(
    full_reset: bool = True,
    keys: Optional[List[str]] = None,
    preserve_keys: Optional[List[str]] = None,
):
    """
    Reset session state on first page load.

    Args:
        full_reset:
            - If True, clear *all* session state except those in preserve_keys.
            - If False, only delete the keys in `keys`.
        keys: list of keys to delete when full_reset=False.
        preserve_keys: list of keys to keep when full_reset=True.
    """
    if "page_loaded" not in st.session_state:
        if full_reset:
            # preserve any keys you want to keep (e.g. api_key)
            preserved = {
                k: st.session_state[k]
                for k in (preserve_keys or [])
                if k in st.session_state
            }
            st.session_state.clear()
            st.session_state.update(preserved)
        else:
            for k in (keys or []):
                st.session_state.pop(k, None)

        st.session_state.page_loaded = True

        # bump the query param via the new API
        params = st.query_params  # get existing
        params["dummy"] = str(uuid.uuid4())
        st.query_params = params