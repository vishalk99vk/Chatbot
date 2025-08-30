import streamlit as st
from streamlit_autorefresh import st_autorefresh
import os
import json
import time
import uuid

# ---------------- CONFIG ----------------
CHAT_DIR = "chats"
USER_DB = "users.json"
ADMIN_PASSWORD = "admin123"   # Change this!
BOT_REPLY = "🤖 Auto-reply: Our admin will get back to you shortly."
REFRESH_INTERVAL = 2000  # ms

if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

# ---------------- Helper Functions ----------------
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

def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=2)

def get_all_users():
    return [f.replace(".json", "") for f in os.listdir(CHAT_DIR) if f.endswith(".json")]

def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def add_message(user_id, role, message, file_path=None):
    chat = load_chat(user_id)
    chat.append({
        "role": role,
        "message": message,
        "time": timestamp(),
        "file": file_path,
        "read": False if role == "user" else True  # admin messages auto-mark read
    })
    save_chat(user_id, chat)

def mark_as_read(user_id):
    chat = load_chat(user_id)
    updated = False
    for msg in chat:
        if msg["role"] == "user":
            msg["read"] = True
            updated = True
    if updated:
        save_chat(user_id, chat)

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="💬 Live Chat", layout="wide")

# Auto refresh by default
st_autorefresh(interval=REFRESH_INTERVAL, key="refresh")

st.title("💬 Live Chat System")

menu = st.sidebar.radio("Login as:", ["User", "Admin"])

# ---------------- USER SECTION ----------------
if menu == "User":
    tabs = st.tabs(["🔑 Login", "📝 Register"])

    # ---- Register ----
    with tabs[1]:
        st.subheader("Create New Account")
        new_user = st.text_input("Choose a User ID:")
        new_pass = st.text_input("Set Password:", type="password")
        if st.button("Register"):
            users = load_users()
            if new_user in users:
                st.error("⚠️ User already exists!")
            else:
                users[new_user] = {"password": new_pass}
                save_users(users)
                st.success("✅ Registered successfully! Please login.")

    # ---- Login ----
    with tabs[0]:
        st.subheader("Login")
        user_id = st.text_input("User ID:")
        user_pass = st.text_input("Password:", type="password")
        if st.button("Login"):
            users = load_users()
            if user_id in users and users[user_id]["password"] == user_pass:
                st.session_state["user_logged_in"] = True
                st.session_state["user_id"] = user_id
                st.success("✅ Logged in!")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid credentials")

    # ---- Chat Window ----
    if st.session_state.get("user_logged_in", False):
        user_id = st.session_state["user_id"]
        st.subheader(f"Chat - {user_id}")
        chat_history = load_chat(user_id)

        for chat in chat_history:
            msg_time = chat.get("time", "")
            if chat["role"] == "user":
                st.markdown(f"<div style='text-align:right; color:blue;'>🧑‍💻 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:left; color:green;'>👨‍💼 Admin ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

            if chat.get("file"):
                with open(chat["file"], "rb") as f:
                    st.download_button("⬇️ Download File", f, file_name=os.path.basename(chat["file"]))

        user_msg = st.text_input("Type your message:")
        user_file = st.file_uploader("Upload a file:", key=str(uuid.uuid4()))
        if st.button("Send"):
            file_path = None
            if user_file:
                file_path = os.path.join(CHAT_DIR, f"{uuid.uuid4()}_{user_file.name}")
                with open(file_path, "wb") as f:
                    f.write(user_file.read())
            if user_msg or file_path:
                add_message(user_id, "user", user_msg, file_path)
                st.experimental_rerun()

# ---------------- ADMIN SECTION ----------------
elif menu == "Admin":
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        pwd = st.text_input("Enter Admin Password:", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("✅ Logged in as Admin")
                st.experimental_rerun()
            else:
                st.error("❌ Wrong Password")

    else:
        if st.button("🚪 Logout"):
            st.session_state.admin_authenticated = False
            st.experimental_rerun()

        user_list = get_all_users()
        if user_list:
            # Show unread indicator
            unread_badges = []
            for u in user_list:
                chat = load_chat(u)
                unread = any(not msg.get("read", True) for msg in chat if msg["role"] == "user")
                if unread:
                    unread_badges.append(f"🔴 {u}")
                else:
                    unread_badges.append(u)

            selected_user = st.selectbox("Select a user:", unread_badges)
            selected_user = selected_user.replace("🔴 ", "")

            chat_history = load_chat(selected_user)

            st.markdown(f"### Chat with {selected_user}")
            for chat in chat_history:
                msg_time = chat.get("time", "")
                if chat["role"] == "user":
                    st.markdown(f"<div style='text-align:left; color:blue;'>🧑‍💻 User ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:right; color:green;'>👨‍💼 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

                if chat.get("file"):
                    with open(chat["file"], "rb") as f:
                        st.download_button("⬇️ Download File", f, file_name=os.path.basename(chat["file"]))

            # Reply box
            admin_msg = st.text_input("Your Reply:")
            admin_file = st.file_uploader("Upload a file (Admin):", key=str(uuid.uuid4()))
            if st.button("Send Reply"):
                file_path = None
                if admin_file:
                    file_path = os.path.join(CHAT_DIR, f"{uuid.uuid4()}_{admin_file.name}")
                    with open(file_path, "wb") as f:
                        f.write(admin_file.read())
                if admin_msg or file_path:
                    add_message(selected_user, "admin", admin_msg, file_path)
                    mark_as_read(selected_user)
                    st.experimental_rerun()

            # Delete chat option
            if st.button("🗑️ Delete Chat"):
                os.remove(get_chat_path(selected_user))
                st.warning("Chat deleted!")
                st.experimental_rerun()

            # AI Auto-reply after 3 mins if no admin response
            if chat_history and chat_history[-1]["role"] == "user":
                last_msg_time = time.mktime(time.strptime(chat_history[-1]["time"], "%Y-%m-%d %H:%M:%S"))
                if time.time() - last_msg_time > 180:  # 3 minutes
                    add_message(selected_user, "admin", BOT_REPLY)
                    mark_as_read(selected_user)
                    st.experimental_rerun()

        else:
            st.info("No users have started a chat yet.")
