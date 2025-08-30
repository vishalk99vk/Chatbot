import streamlit as st
import os
import json
import time
import hashlib

CHAT_DIR = "chats"
UPLOAD_DIR = "uploads"
USER_FILE = "users.json"
ADMIN_PASSWORD = "admin123"  # change this

if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- Helper Functions ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

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
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# --- Streamlit App ---
st.set_page_config(page_title="Live Chat", layout="wide")
st.title("💬 Live Chat System (User ↔ Admin + AI Bot)")

# Auto-refresh always enabled
st.experimental_autorefresh(interval=2000, key="refresh")

menu = st.sidebar.radio("Login as:", ["User", "Admin"])

# --- User Section ---
if menu == "User":
    tabs = st.tabs(["🔑 Login", "📝 Register"])

    with tabs[1]:  # Register
        new_user = st.text_input("Choose a User ID:", key="reg_user")
        new_pass = st.text_input("Set Password:", type="password", key="reg_pass")
        if st.button("Register"):
            users = load_users()
            if new_user in users:
                st.error("❌ User already exists!")
            else:
                users[new_user] = hash_password(new_pass)
                save_users(users)
                st.success("✅ Registered successfully! Now login.")

    with tabs[0]:  # Login
        user_id = st.text_input("User ID:", key="login_user")
        user_pass = st.text_input("Password:", type="password", key="login_pass")
        if st.button("Login", key="user_login"):
            users = load_users()
            if user_id in users and users[user_id] == hash_password(user_pass):
                st.session_state["user_authenticated"] = user_id
                st.success("✅ Logged in successfully!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    if "user_authenticated" in st.session_state:
        user_id = st.session_state.user_authenticated
        chat_history = load_chat(user_id)

        st.markdown("### Chat Window")
        for chat in chat_history:
            msg_time = chat.get("time", "")
            if chat["role"] == "user":
                st.markdown(f"<div style='text-align:right; color:blue;'>🧑‍💻 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
            elif chat["role"] == "admin":
                st.markdown(f"<div style='text-align:left; color:green;'>👨‍💼 Admin ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:left; color:purple;'>🤖 AI Bot ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

        user_msg = st.text_input("Type your message:", key="user_input")
        if st.button("Send", key="user_send"):
            if user_msg:
                chat_history.append({"role": "user", "message": user_msg, "time": timestamp()})
                save_chat(user_id, chat_history)
                st.rerun()

        # File upload by user
        st.markdown("### 📂 Share a File with Admin")
        uploaded_file = st.file_uploader("Upload a file", key="user_file")
        if uploaded_file:
            user_dir = os.path.join(UPLOAD_DIR, user_id)
            os.makedirs(user_dir, exist_ok=True)
            file_path = os.path.join(user_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ File {uploaded_file.name} uploaded!")

        # List downloadable files (from admin)
        user_dir = os.path.join(UPLOAD_DIR, user_id)
        if os.path.exists(user_dir):
            st.markdown("### 📥 Files from Admin")
            for fname in os.listdir(user_dir):
                file_path = os.path.join(user_dir, fname)
                with open(file_path, "rb") as f:
                    st.download_button(f"⬇️ Download {fname}", f, file_name=fname)


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
        if user_list:
            selected_user = st.selectbox("Select a user:", user_list)
            chat_history = load_chat(selected_user)

            st.markdown(f"### Chat with {selected_user}")
            for chat in chat_history:
                msg_time = chat.get("time", "")
                if chat["role"] == "user":
                    st.markdown(f"<div style='text-align:left; color:blue;'>🧑‍💻 User ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
                elif chat["role"] == "admin":
                    st.markdown(f"<div style='text-align:right; color:green;'>👨‍💼 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:left; color:purple;'>🤖 AI Bot ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

            # Reply box
            admin_reply = st.text_input("Your Reply:", key="admin_reply")
            if st.button("Send Reply"):
                if admin_reply:
                    chat_history.append({"role": "admin", "message": admin_reply, "time": timestamp()})
                    save_chat(selected_user, chat_history)
                    st.rerun()

            # File upload by admin
            st.markdown("### 📂 Share a File with User")
            admin_file = st.file_uploader("Upload a file", key="admin_file")
            if admin_file:
                user_dir = os.path.join(UPLOAD_DIR, selected_user)
                os.makedirs(user_dir, exist_ok=True)
                file_path = os.path.join(user_dir, admin_file.name)
                with open(file_path, "wb") as f:
                    f.write(admin_file.getbuffer())
                st.success(f"✅ File {admin_file.name} uploaded for {selected_user}!")

            # List downloadable files (from user)
            user_dir = os.path.join(UPLOAD_DIR, selected_user)
            if os.path.exists(user_dir):
                st.markdown("### 📥 Files from User")
                for fname in os.listdir(user_dir):
                    file_path = os.path.join(user_dir, fname)
                    with open(file_path, "rb") as f:
                        st.download_button(f"⬇️ Download {fname}", f, file_name=fname)

            # Delete chat option
            if st.button("🗑️ Delete Chat"):
                os.remove(get_chat_path(selected_user))
                st.success("Chat deleted!")
                st.rerun()
        else:
            st.info("No users have started a chat yet.")
