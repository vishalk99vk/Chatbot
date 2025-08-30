import streamlit as st
import os
import json
import time
from streamlit_autorefresh import st_autorefresh

CHAT_DIR = "chats"
UPLOAD_DIR = "uploads"
ADMIN_PASSWORD = "admin123"  # change this

# Ensure directories exist
os.makedirs(CHAT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Helper Functions ---
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

def get_unread_users():
    """Users whose last message is from the user (not admin)"""
    unread = []
    for u in get_all_users():
        chats = load_chat(u)
        if chats and chats[-1]["role"] == "user":
            unread.append(u)
    return unread

def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def render_message(role, message, msg_time, file_path=None):
    """Pretty chat bubbles like WhatsApp, with optional file/image"""
    if role == "user":
        align = "right"
        color = "#DCF8C6"
        sender = "🧑‍💻 You"
    else:
        align = "left"
        color = "#EDEDED"
        sender = "👨‍💼 Admin"

    # Chat bubble
    st.markdown(
        f"""
        <div style="text-align:{align}; margin:6px;">
            <div style="background-color:{color}; padding:10px; border-radius:10px; display:inline-block; max-width:70%;">
                {message}
            </div><br>
            <small>{sender} • {msg_time}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # File/image handling
    if file_path and os.path.exists(file_path):
        filename = os.path.basename(file_path)
        # If it's an image, show preview
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            st.image(file_path, caption=filename, use_column_width=True)
        # Download button for all files
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        st.download_button(
            label=f"📎 Download {filename}",
            data=file_bytes,
            file_name=filename,
            mime="application/octet-stream",
        )


# --- Streamlit App ---
st.set_page_config(page_title="Live Chat", layout="wide")
st.title("💬 Live Chat System (User ↔ Admin)")

menu = st.sidebar.radio("Login as:", ["User", "Admin"])

# Auto-refresh every 2 seconds for live effect
st_autorefresh_enabled = st.sidebar.checkbox("🔄 Auto-refresh every 2s", value=True)
if st_autorefresh_enabled:
    st_autorefresh(interval=2000, key="refresh")


# --- User Section ---
if menu == "User":
    user_id = st.text_input("Enter your User ID (any unique name):")
    if user_id:
        chat_history = load_chat(user_id)

        st.markdown("### Chat Window")
        for chat in chat_history:
            render_message(chat["role"], chat["message"], chat.get("time", ""), chat.get("file"))

        user_msg = st.text_input("Type your message:", key="user_input")
        uploaded_file = st.file_uploader("Upload a file (optional):", key="user_file")

        if st.button("Send", key="user_send"):
            if user_msg or uploaded_file:
                file_path = None
                if uploaded_file:
                    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                chat_history.append({
                    "role": "user",
                    "message": user_msg if user_msg else "",
                    "time": timestamp(),
                    "file": file_path
                })
                save_chat(user_id, chat_history)
                st.session_state.user_input = ""  # clear text box
                st.rerun()


# --- Admin Section ---
elif menu == "Admin":
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
            st.rerun()

        user_list = get_all_users()
        unread_users = get_unread_users()

        if user_list:
            # Mark unread users with 🔴
            user_labels = [f"{u} 🔴" if u in unread_users else u for u in user_list]
            selected_user = st.selectbox("Select a user:", user_labels)
            selected_user = selected_user.replace(" 🔴", "")  # cleanup label

            chat_history = load_chat(selected_user)

            st.markdown(f"### Chat with {selected_user}")
            for chat in chat_history:
                render_message(chat["role"], chat["message"], chat.get("time", ""), chat.get("file"))

            # Reply box
            admin_reply = st.text_input("Your Reply:", key="admin_reply")
            admin_file = st.file_uploader("Upload a file (optional):", key="admin_file")

            if st.button("Send Reply"):
                if admin_reply or admin_file:
                    file_path = None
                    if admin_file:
                        file_path = os.path.join(UPLOAD_DIR, admin_file.name)
                        with open(file_path, "wb") as f:
                            f.write(admin_file.getbuffer())

                    chat_history.append({
                        "role": "admin",
                        "message": admin_reply if admin_reply else "",
                        "time": timestamp(),
                        "file": file_path
                    })
                    save_chat(selected_user, chat_history)
                    st.session_state.admin_reply = ""  # clear text box
                    st.rerun()
        else:
            st.info("No users have started a chat yet.")
