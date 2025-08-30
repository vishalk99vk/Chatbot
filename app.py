import streamlit as st
import os
import json
from datetime import datetime
import base64

# -------------------------
# Setup
# -------------------------
CHAT_DIR = "chats"
UPLOAD_DIR = "uploads"
ADMIN_PASSWORD = "admin123"  # change for security

os.makedirs(CHAT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -------------------------
# Helper Functions
# -------------------------
def get_chat_file(user_id):
    return os.path.join(CHAT_DIR, f"{user_id}.json")

def load_chat(user_id):
    file_path = get_chat_file(user_id)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

def save_chat(user_id, chat_history):
    with open(get_chat_file(user_id), "w") as f:
        json.dump(chat_history, f, indent=2)

def get_all_users():
    return [f.replace(".json", "") for f in os.listdir(CHAT_DIR)]

def format_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# -------------------------
# Streamlit Page Config
# -------------------------
st.set_page_config(page_title="Live Chat System", layout="wide")
st.autorefresh(interval=1000, key="refresh")  # ✅ Auto refresh 1s

st.title("💬 Real-Time Chat System")

# -------------------------
# Step 1: Role Selection
# -------------------------
if "role" not in st.session_state:
    role = st.radio("Who are you?", ["User", "Admin"])
    if st.button("Proceed"):
        st.session_state.role = role
        st.rerun()
else:
    role = st.session_state.role

# -------------------------
# USER PANEL
# -------------------------
if role == "User":
    st.subheader("👤 User Panel")
    user_id = st.text_input("Enter your User ID:", value="guest")

    if user_id:
        chat_history = load_chat(user_id)

        # Display chat
        st.markdown("### Chat History")
        for chat in chat_history:
            if chat["role"] == "user":
                st.markdown(f"🧑 **You** ({chat['time']}): {chat['message']}")
            elif chat["role"] == "admin":
                st.markdown(f"👨‍💻 **Admin** ({chat['time']}): {chat['message']}")
            elif chat["role"] == "file":
                file_link = chat['file']
                st.markdown(f"📎 **File uploaded at {chat['time']}** → {file_link}")

        # Message box
        msg = st.text_input("Type your message:")
        if st.button("Send Message"):
            if msg:
                chat_history.append({"role": "user", "message": msg, "time": format_time()})
                save_chat(user_id, chat_history)
                st.rerun()

        # File upload
        uploaded_file = st.file_uploader("Upload a file", type=None)
        if uploaded_file:
            if uploaded_file.size > 200 * 1024 * 1024:  # 200 MB
                st.error("🚨 Please upload this file to Google Drive and share the link instead.")
            else:
                file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                file_url = f"[📂 Download {uploaded_file.name}](./{file_path})"
                chat_history.append({"role": "file", "file": file_url, "time": format_time()})
                save_chat(user_id, chat_history)
                st.success("✅ File uploaded & sent to Admin.")
                st.rerun()

# -------------------------
# ADMIN PANEL
# -------------------------
elif role == "Admin":
    st.subheader("👨‍💻 Admin Panel")

    # Admin authentication
    if "admin_authenticated" not in st.session_state:
        pwd = st.text_input("Enter Admin Password:", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Wrong password")

    if st.session_state.get("admin_authenticated", False):
        users = get_all_users()
        if users:
            selected_user = st.selectbox("Select a user:", users)
            chat_history = load_chat(selected_user)

            st.markdown(f"### Chat with {selected_user}")
            for chat in chat_history:
                if chat["role"] == "user":
                    st.markdown(f"🧑 **User** ({chat['time']}): {chat['message']}")
                elif chat["role"] == "admin":
                    st.markdown(f"👨‍💻 **You** ({chat['time']}): {chat['message']}")
                elif chat["role"] == "file":
                    st.markdown(f"📎 **File uploaded at {chat['time']}** → {chat['file']}")

            # Reply box
            admin_reply = st.text_input("Your reply:")
            if st.button("Send Reply"):
                if admin_reply:
                    chat_history.append({"role": "admin", "message": admin_reply, "time": format_time()})
                    save_chat(selected_user, chat_history)
                    st.rerun()

        else:
            st.info("No users have started chatting yet.")
