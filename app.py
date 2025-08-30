import streamlit as st
import os
import json
import time

# --- Constants ---
CHAT_DIR = "chats"
UPLOAD_DIR = "uploads"
USER_FILE = "users.json"
ADMIN_PASSWORD = "Vishal@12345"  # change this

# --- Setup Directories ---
for d in [CHAT_DIR, UPLOAD_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# --- Helper Functions ---
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

# --- AI Bot Reply ---
def maybe_bot_reply(user_id, chat_history):
    if not chat_history:
        return chat_history
    last_msg = chat_history[-1]
    if last_msg["role"] == "user":
        msg_time = last_msg.get("time", timestamp())
        msg_ts = time.mktime(time.strptime(msg_time, "%Y-%m-%d %H:%M:%S"))
        if time.time() - msg_ts > 180:  # 3 minutes
            chat_history.append({
                "role": "bot",
                "message": "🤖 Our admin is busy right now, but we’ll get back soon!",
                "time": timestamp()
            })
            save_chat(user_id, chat_history)
    return chat_history

# --- Streamlit App ---
st.set_page_config(page_title="Live Chat", layout="wide")
st.title("💬 Live Chat System (User ↔ Admin + Bot)")

menu = st.sidebar.radio("Login as:", ["User", "Admin"])

# --- User Section ---
if menu == "User":
    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

    with tab_register:
        st.subheader("Create a new account")
        new_user = st.text_input("Choose a User ID:", key="reg_user")
        new_pwd = st.text_input("Choose a Password:", type="password", key="reg_pwd")
        if st.button("Register"):
            users = load_users()
            if new_user in users:
                st.error("⚠️ User already exists!")
            else:
                users[new_user] = new_pwd
                save_users(users)
                st.success("✅ Registered successfully! You can now login.")

    with tab_login:
        st.subheader("Login to your account")
        user_id = st.text_input("User ID:", key="login_user")
        pwd = st.text_input("Password:", type="password", key="login_pwd")
        if st.button("Login", key="user_login"):
            users = load_users()
            if user_id in users and users[user_id] == pwd:
                st.session_state.user_authenticated = True
                st.session_state.user_id = user_id
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    if st.session_state.get("user_authenticated", False):
        user_id = st.session_state.user_id
        st.success(f"Logged in as {user_id}")

        chat_history = load_chat(user_id)
        chat_history = maybe_bot_reply(user_id, chat_history)

        st.markdown("### Chat Window")
        for chat in chat_history:
            msg_time = chat.get("time", "")
            if chat["role"] == "user":
                st.markdown(f"<div style='text-align:right; color:blue;'>🧑‍💻 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
            elif chat["role"] == "admin":
                st.markdown(f"<div style='text-align:left; color:green;'>👨‍💼 Admin ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:left; color:orange;'>🤖 Bot ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

        # Message box
        user_msg = st.text_input("Type your message:", key="user_input")
        if st.button("Send", key="user_send"):
            if user_msg:
                chat_history.append({"role": "user", "message": user_msg, "time": timestamp()})
                save_chat(user_id, chat_history)
                st.rerun()

        # File upload
        uploaded_file = st.file_uploader("Upload a file")
        if uploaded_file:
            file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{uploaded_file.name}")
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Uploaded {uploaded_file.name}")
            st.download_button("⬇️ Download your file", data=open(file_path, "rb"), file_name=uploaded_file.name)

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
                    st.markdown(f"<div style='text-align:right; color:orange;'>🤖 Bot ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

            admin_reply = st.text_input("Your Reply:", key="admin_reply")
            if st.button("Send Reply"):
                if admin_reply:
                    chat_history.append({"role": "admin", "message": admin_reply, "time": timestamp()})
                    save_chat(selected_user, chat_history)
                    st.rerun()

            # Delete chat
            if st.button("🗑️ Delete Chat"):
                os.remove(get_chat_path(selected_user))
                st.success("Chat deleted!")
                st.rerun()

            # Uploaded files
            st.subheader("📂 User Files")
            for file in os.listdir(UPLOAD_DIR):
                if file.startswith(selected_user + "_"):
                    st.download_button(f"⬇️ {file}", data=open(os.path.join(UPLOAD_DIR, file), "rb"), file_name=file.split("_", 1)[1])
        else:
            st.info("No users have started a chat yet.")
