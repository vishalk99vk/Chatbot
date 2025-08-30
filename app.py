import os
import json
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ===================== CONFIG ===================== #
st.set_page_config(page_title="Live Chat System", layout="wide")
CHAT_FILE = "chat_data.json"

# ===================== UTILITIES ===================== #
def load_chat():
    """Load chat history from file."""
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            return json.load(f)
    return []

def save_chat(chat):
    """Save chat history to file."""
    with open(CHAT_FILE, "w") as f:
        json.dump(chat, f)

# ===================== AUTO REFRESH ===================== #
st_autorefresh(interval=1000, key="refresh")  # Auto refresh every 1s

# ===================== LOGIN PANEL ===================== #
if "role" not in st.session_state:
    st.title("🔐 Login Panel")
    role = st.radio("Who are you?", ["User", "Admin"])
    if st.button("Proceed"):
        st.session_state.role = role
        st.rerun()
    st.stop()

role = st.session_state.role
st.sidebar.title("⚙️ Options")
if st.sidebar.button("🔄 Logout"):
    st.session_state.clear()
    st.rerun()

st.title(f"💬 Live Chat - {role} Panel")

# ===================== LOAD CHAT ===================== #
chat_history = load_chat()

# ===================== SHOW CHAT ===================== #
st.markdown("### 📜 Chat History")
for msg in chat_history:
    if msg["sender"] == "User":
        st.markdown(
            f"<div style='background:#e6f7ff; padding:10px; border-radius:10px; margin:5px 0;'><b>User:</b> {msg['text']}</div>",
            unsafe_allow_html=True,
        )
        if msg.get("file"):
            st.write("📂 File uploaded by User:")
            st.download_button(
                label=f"Download {msg['file']['name']}",
                data=bytes.fromhex(msg["file"]["data"]),
                file_name=msg["file"]["name"],
            )

    else:  # Admin message
        st.markdown(
            f"<div style='background:#fff0f6; padding:10px; border-radius:10px; margin:5px 0; text-align:right;'><b>Admin:</b> {msg['text']}</div>",
            unsafe_allow_html=True,
        )

# ===================== INPUT SECTION ===================== #
st.markdown("### ✏️ Send a Message")

with st.form("chat_form", clear_on_submit=True):
    message = st.text_input("Type your message...")
    uploaded_file = st.file_uploader("Upload a file (optional)", type=None)

    submitted = st.form_submit_button("Send")
    if submitted and (message.strip() or uploaded_file):
        new_msg = {"sender": role, "text": message.strip(), "file": None}

        # Handle file upload
        if uploaded_file:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if file_size_mb > 200:
                st.warning("⚠️ Please upload this file to Google Drive and share the link (file > 200 MB).")
            else:
                file_data = uploaded_file.read()
                new_msg["file"] = {
                    "name": uploaded_file.name,
                    "data": file_data.hex()
                }

        chat_history.append(new_msg)
        save_chat(chat_history)
        st.rerun()
