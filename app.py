import streamlit as st
import os
import json
import time
import base64

CHAT_DIR = "chats"
UPLOAD_DIR = "uploads"
ADMIN_PASSWORD = "Vishal@9999"  # change this

os.makedirs(CHAT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Helpers ---
def get_chat_path(user_id):
    return os.path.join(CHAT_DIR, f"{user_id}.json")

def load_chat(user_id):
    path = get_chat_path(user_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def save_chat(user_id, chat_history):
    path = get_chat_path(user_id)
    with open(path, "w") as f:
        json.dump(chat_history, f, indent=2)

def get_all_users():
    return [f.replace(".json", "") for f in os.listdir(CHAT_DIR) if f.endswith(".json")]

def timestamp():
    return time.strftime("%H:%M", time.localtime())

def render_message(role, msg, msg_time):
    """WhatsApp-style bubbles"""
    if role == "user":
        st.markdown(
            f"""
            <div style='display:flex; justify-content:flex-end; margin:5px;'>
                <div style='background-color:#DCF8C6; padding:10px 15px; border-radius:15px; max-width:70%; text-align:right;'>
                    <b>You:</b> {msg}<br>
                    <small style='color:gray;'>{msg_time}</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style='display:flex; justify-content:flex-start; margin:5px;'>
                <div style='background-color:#E1F3FB; padding:10px 15px; border-radius:15px; max-width:70%; text-align:left;'>
                    <b>Admin:</b> {msg}<br>
                    <small style='color:gray;'>{msg_time}</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# --- Streamlit ---
st.set_page_config(page_title="Live Chat", layout="wide")

st.title("💬 WhatsApp-Style Chat System")

# Step 1: Pre-login role selection
if "role_selected" not in st.session_state:
    st.session_state.role_selected = None

if not st.session_state.role_selected:
    choice = st.radio("Who are you?", ["User", "Admin"])
    if st.button("Proceed"):
        st.session_state.role_selected = choice
        st.rerun()

# Auto-refresh every 1 second
if st.session_state.role_selected:
    st_autorefresh = st.sidebar.checkbox("🔄 Auto-refresh every 1s", value=True)
    if st_autorefresh:
        st.experimental_autorefresh(interval=1000, key="refresh")

# --- User Section ---
if st.session_state.role_selected == "User":
    user_id = st.text_input("Enter your User ID (any unique name):")
    if user_id:
        chat_history = load_chat(user_id)

        if "last_seen_user" not in st.session_state:
            st.session_state.last_seen_user = 0

        st.markdown("### Chat Window")
        for chat in chat_history:
            render_message(chat["role"], chat["message"], chat.get("time", ""))

        if len(chat_history) > st.session_state.last_seen_user:
            if chat_history[-1]["role"] == "admin":
                st.audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg")
        st.session_state.last_seen_user = len(chat_history)

        # User input message
        user_msg = st.text_input("Type your message:", key="user_input")
        if st.button("Send", key="user_send"):
            if user_msg:
                chat_history.append({"role": "user", "message": user_msg, "time": timestamp()})
                save_chat(user_id, chat_history)
                st.rerun()

        # File upload
        uploaded_file = st.file_uploader("📂 Upload a file (image/pdf/excel/etc.)")
        if uploaded_file:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if file_size_mb > 200:
                st.warning("⚠️ Please upload this file on Google Drive and share the link.")
            else:
                file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                file_link = f"📎 Uploaded File: {uploaded_file.name}"
                chat_history.append({"role": "user", "message": file_link, "time": timestamp()})
                save_chat(user_id, chat_history)
                st.success("✅ File uploaded and sent!")
                st.rerun()


# --- Admin Section ---
elif st.session_state.role_selected == "Admin":
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        pwd = st.text_input("Enter Admin Password:", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("✅ Logged in as Admin")
                st.rerun()
            else:
                st.error("❌ Wrong Password")

    else:
        if st.button("🚪 Logout"):
            st.session_state.admin_authenticated = False
            st.session_state.role_selected = None
            st.rerun()

        user_list = get_all_users()
        if user_list:
            selected_user = st.selectbox("Select a user:", user_list)
            chat_history = load_chat(selected_user)

            if "last_seen_admin" not in st.session_state:
                st.session_state.last_seen_admin = {}

            if selected_user not in st.session_state.last_seen_admin:
                st.session_state.last_seen_admin[selected_user] = 0

            st.markdown(f"### Chat with {selected_user}")
            for chat in chat_history:
                render_message(chat["role"], chat["message"], chat.get("time", ""))

            if len(chat_history) > st.session_state.last_seen_admin[selected_user]:
                if chat_history[-1]["role"] == "user":
                    st.audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg")
            st.session_state.last_seen_admin[selected_user] = len(chat_history)

            # Reply box
            admin_reply = st.text_input("Your Reply:", key="admin_reply")
            if st.button("Send Reply"):
                if admin_reply:
                    chat_history.append({"role": "admin", "message": admin_reply, "time": timestamp()})
                    save_chat(selected_user, chat_history)
                    st.rerun()
        else:
            st.info("No users have started a chat yet.")
