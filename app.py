import streamlit as st
import os
import json
import time
from streamlit_autorefresh import st_autorefresh

# ------------------- Config -------------------
CHAT_DIR = "chats"
USER_FILE = "users.json"
ADMIN_PASSWORD = "Vishal@12345"  # change this

if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

# ------------------- Helper Functions -------------------
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

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

def ai_bot_reply(user_id, chat_history):
    """Auto reply if no admin response for 3 minutes"""
    if not chat_history:
        return
    last_msg = chat_history[-1]
    if last_msg["role"] == "user":
        last_time = time.mktime(time.strptime(last_msg["time"], "%Y-%m-%d %H:%M:%S"))
        if time.time() - last_time > 180:  # 3 minutes
            chat_history.append({
                "role": "admin",
                "message": "🤖 This is an AI auto-reply. The admin will respond shortly.",
                "time": timestamp()
            })
            save_chat(user_id, chat_history)

# ------------------- Streamlit UI -------------------
st.set_page_config(page_title="💬 Live Chat", layout="wide")
st.title("💬 Live Chat System (User ↔ Admin + AI Bot)")

menu = st.sidebar.radio("Login as:", ["Register", "User", "Admin"])

# Auto-refresh
st_autorefresh_enabled = st.sidebar.checkbox("🔄 Auto-refresh every 2s", value=True)
if st_autorefresh_enabled:
    st_autorefresh(interval=2000, key="refresh")

# ------------------- Register Section -------------------
if menu == "Register":
    st.subheader("📝 Register New Account")
    new_user = st.text_input("Choose a User ID:")
    new_pass = st.text_input("Choose a Password:", type="password")

    if st.button("Register"):
        users = load_users()
        if new_user in users:
            st.error("❌ User ID already exists. Choose another.")
        elif new_user.strip() == "" or new_pass.strip() == "":
            st.error("❌ User ID and Password cannot be empty.")
        else:
            users[new_user] = new_pass
            save_users(users)
            st.success("✅ Registered successfully! Go to 'User' tab to login.")

# ------------------- User Section -------------------
elif menu == "User":
    st.subheader("👤 User Login")
    user_id = st.text_input("User ID:")
    pwd = st.text_input("Password:", type="password")

    if "user_authenticated" not in st.session_state:
        st.session_state.user_authenticated = False
        st.session_state.active_user = None

    if st.button("Login"):
        users = load_users()
        if user_id in users and users[user_id] == pwd:
            st.session_state.user_authenticated = True
            st.session_state.active_user = user_id
            st.success(f"✅ Logged in as {user_id}")
            st.rerun()
        else:
            st.error("❌ Wrong credentials")

    if st.session_state.user_authenticated and st.session_state.active_user:
        user_id = st.session_state.active_user
        chat_history = load_chat(user_id)

        st.markdown("### 💬 Chat Window")
        for chat in chat_history:
            msg_time = chat.get("time", "")
            if chat["role"] == "user":
                st.markdown(f"<div style='text-align:right; color:blue;'>🧑‍💻 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:left; color:green;'>👨‍💼 Admin ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

        user_msg = st.text_input("Type your message:", key="user_input")
        if st.button("Send", key="user_send"):
            if user_msg:
                chat_history.append({"role": "user", "message": user_msg, "time": timestamp()})
                save_chat(user_id, chat_history)
                st.rerun()

        # File upload
        uploaded_file = st.file_uploader("📎 Upload a file")
        if uploaded_file:
            file_path = os.path.join(CHAT_DIR, f"{user_id}_{uploaded_file.name}")
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            chat_history.append({"role": "user", "message": f"📎 Sent file: {uploaded_file.name}", "time": timestamp()})
            save_chat(user_id, chat_history)
            st.success(f"✅ File {uploaded_file.name} uploaded successfully.")
            st.rerun()

        # Show uploaded files
        st.markdown("### 📂 Your Uploaded Files")
        for file in os.listdir(CHAT_DIR):
            if file.startswith(user_id + "_"):
                with open(os.path.join(CHAT_DIR, file), "rb") as f:
                    st.download_button(f"⬇️ Download {file}", f, file_name=file)

        if st.button("🚪 Logout"):
            st.session_state.user_authenticated = False
            st.session_state.active_user = None
            st.rerun()

# ------------------- Admin Section -------------------
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

            # AI auto reply check
            ai_bot_reply(selected_user, chat_history)
            chat_history = load_chat(selected_user)

            st.markdown(f"### 💬 Chat with {selected_user}")
            for chat in chat_history:
                msg_time = chat.get("time", "")
                if chat["role"] == "user":
                    st.markdown(f"<div style='text-align:left; color:blue;'>🧑‍💻 User ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:right; color:green;'>👨‍💼 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

            admin_reply = st.text_input("Your Reply:", key="admin_reply")
            if st.button("Send Reply"):
                if admin_reply:
                    chat_history.append({"role": "admin", "message": admin_reply, "time": timestamp()})
                    save_chat(selected_user, chat_history)
                    st.rerun()

            # Admin delete chat
            if st.button("🗑️ Delete Chat"):
                os.remove(get_chat_path(selected_user))
                st.success(f"✅ Deleted chat with {selected_user}")
                st.rerun()

            # Download user files
            st.markdown("### 📂 User Files")
            for file in os.listdir(CHAT_DIR):
                if file.startswith(selected_user + "_"):
                    with open(os.path.join(CHAT_DIR, file), "rb") as f:
                        st.download_button(f"⬇️ Download {file}", f, file_name=file)

        else:
            st.info("No users have started a chat yet.")
