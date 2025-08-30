import streamlit as st
import os
import json
import hashlib
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# -----------------------------
# CONFIG
# -----------------------------
USERS_FILE = "users.json"
CHATS_DIR = "chats"
ADMIN_USERNAME = "oyeduggu"

if not os.path.exists(CHATS_DIR):
    os.makedirs(CHATS_DIR)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_chat_file(username):
    return os.path.join(CHATS_DIR, f"{username}.json")

def load_chat(username):
    chat_file = get_chat_file(username)
    if os.path.exists(chat_file):
        with open(chat_file, "r") as f:
            return json.load(f)
    return []

def save_chat(username, chat):
    with open(get_chat_file(username), "w") as f:
        json.dump(chat, f)

def add_message(username, sender, message, file_path=None):
    chat = load_chat(username)
    chat.append({
        "sender": sender,
        "message": message,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file": file_path,
        "read": sender == username  # Mark as read if it's user sending
    })
    save_chat(username, chat)

# -----------------------------
# AUTH SYSTEM
# -----------------------------
if "user" not in st.session_state:
    st.session_state.user = None

tabs = st.tabs(["Login", "Register"])

with tabs[0]:
    st.subheader("Login")
    login_username = st.text_input("Username", key="login_user")
    login_password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        users = load_users()
        if login_username in users and users[login_username] == hash_password(login_password):
            st.session_state.user = login_username
            st.success(f"Logged in as {login_username}")
        else:
            st.error("Invalid username or password")

with tabs[1]:
    st.subheader("Register")
    reg_username = st.text_input("New Username", key="reg_user")
    reg_password = st.text_input("New Password", type="password", key="reg_pass")
    if st.button("Register"):
        users = load_users()
        if reg_username in users:
            st.error("Username already exists")
        else:
            users[reg_username] = hash_password(reg_password)
            save_users(users)
            st.success("Registered successfully! Please login.")

# -----------------------------
# MAIN APP
# -----------------------------
if st.session_state.user:
    st_autorefresh(interval=3000, key="refresh")  # Auto refresh every 3s
    st.sidebar.title("Menu")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.experimental_rerun()

    username = st.session_state.user

    # ------------------- ADMIN DASHBOARD -------------------
    if username == ADMIN_USERNAME:
        st.title("📢 Admin Dashboard")
        st.write("Select a user to chat with:")

        users = [u for u in load_users().keys() if u != ADMIN_USERNAME]
        for u in users:
            chat = load_chat(u)
            unread = any(msg.get("sender") == u and not msg.get("read", False) for msg in chat)
            red_dot = " 🔴" if unread else ""
            if st.button(f"Chat with {u}{red_dot}"):
                st.session_state.active_chat = u

        if "active_chat" in st.session_state:
            active_user = st.session_state.active_chat
            st.subheader(f"Chat with {active_user}")

            chat = load_chat(active_user)
            for msg in chat:
                sender = msg.get("sender", "unknown")
                time = msg.get("time", "")
                message = msg.get("message", "")
                st.write(f"**{sender}** [{time}]: {message}")

                file_path = msg.get("file")
                if isinstance(file_path, str) and os.path.exists(file_path):
                    file_name = os.path.basename(file_path)
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Download {file_name}",
                            data=f,
                            file_name=file_name,
                            mime="application/octet-stream"
                        )

            admin_msg = st.text_input("Your message", key="admin_msg")
            uploaded_file = st.file_uploader("Send file", key="admin_file")
            if st.button("Send", key="admin_send"):
                file_path = None
                if uploaded_file:
                    file_path = os.path.join(CHATS_DIR, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                add_message(active_user, "admin", admin_msg, file_path)
                st.experimental_rerun()

            if st.button("❌ Delete Chat"):
                os.remove(get_chat_file(active_user))
                st.success("Chat deleted")
                del st.session_state.active_chat
                st.experimental_rerun()

    # ------------------- USER DASHBOARD -------------------
    else:
        st.title(f"💬 Chat with Admin")
        chat = load_chat(username)

        unread = any(msg.get("sender") == "admin" and not msg.get("read", False) for msg in chat)
        if unread:
            st.subheader(f"🔴 You have {sum(1 for msg in chat if msg.get('sender')=='admin' and not msg.get('read',False))} unread message(s)")

        for msg in chat:
            sender = msg.get("sender", "unknown")
            time = msg.get("time", "")
            message = msg.get("message", "")
            st.write(f"**{sender}** [{time}]: {message}")

            file_path = msg.get("file")
            if isinstance(file_path, str) and os.path.exists(file_path):
                file_name = os.path.basename(file_path)
                with open(file_path, "rb") as f:
                    st.download_button(
                        label=f"⬇️ Download {file_name}",
                        data=f,
                        file_name=file_name,
                        mime="application/octet-stream"
                    )

            # Mark admin messages as read
            if msg.get("sender") == "admin":
                msg["read"] = True
        save_chat(username, chat)

        user_msg = st.text_input("Your message", key="user_msg")
        uploaded_file = st.file_uploader("Send file", key="user_file")
        if st.button("Send", key="user_send"):
            file_path = None
            if uploaded_file:
                file_path = os.path.join(CHATS_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            add_message(username, username, user_msg, file_path)
            st.experimental_rerun()
