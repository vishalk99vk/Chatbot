import streamlit as st
import os
import json
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

CHAT_DIR = "chats"
USER_DIR = "users"
ADMIN_PASSWORD = "admin123"  # change this

if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)
if not os.path.exists(USER_DIR):
    os.makedirs(USER_DIR)

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

def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def get_user_file(user_id):
    return os.path.join(USER_DIR, f"{user_id}.json")

def register_user(user_id, password):
    path = get_user_file(user_id)
    if os.path.exists(path):
        return False
    with open(path, "w") as f:
        json.dump({"password": password}, f)
    return True

def validate_user(user_id, password):
    path = get_user_file(user_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            return data.get("password") == password
    return False

def ai_bot_reply(chat_history):
    return "🤖 Auto-reply: The admin is currently unavailable. Please wait, they’ll respond soon."

# --- Streamlit App ---
st.set_page_config(page_title="Live Chat", layout="wide")
st.title("💬 Live Chat System (User ↔ Admin + AI Bot)")

menu = st.sidebar.radio("Login as:", ["User", "Admin"])

# 🔄 Auto-refresh always ON
st_autorefresh(interval=2000, key="refresh")


# --- User Section ---
if menu == "User":
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab2:
        st.subheader("Register")
        new_user = st.text_input("Choose a User ID:")
        new_pass = st.text_input("Choose a Password:", type="password")
        if st.button("Register"):
            if new_user and new_pass:
                if register_user(new_user, new_pass):
                    st.success("✅ Registered successfully! Now login.")
                else:
                    st.error("❌ User already exists.")

    with tab1:
        st.subheader("Login")
        user_id = st.text_input("User ID:")
        user_pass = st.text_input("Password:", type="password")
        if st.button("Login", key="user_login"):
            if validate_user(user_id, user_pass):
                st.session_state["user_id"] = user_id
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    if st.session_state.get("logged_in") and "user_id" in st.session_state:
        user_id = st.session_state["user_id"]
        chat_history = load_chat(user_id)

        st.markdown("### Chat Window")
        for chat in chat_history:
            msg_time = chat.get("time", "")
            if chat["role"] == "user":
                st.markdown(f"<div style='text-align:right; color:blue;'>🧑‍💻 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
            elif chat["role"] == "admin":
                st.markdown(f"<div style='text-align:left; color:green;'>👨‍💼 Admin ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
            else:  # AI bot
                st.markdown(f"<div style='text-align:left; color:purple;'>🤖 Bot ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

        # File Upload
        user_file = st.file_uploader("Upload a file", key="user_file")
        if user_file:
            file_path = os.path.join(CHAT_DIR, f"{user_id}_{user_file.name}")
            with open(file_path, "wb") as f:
                f.write(user_file.getbuffer())
            chat_history.append({"role": "user", "message": f"[📂 File: {user_file.name}]", "file": file_path, "time": timestamp()})
            save_chat(user_id, chat_history)
            st.success("✅ File sent!")
            st.rerun()

        # User message
        user_msg = st.text_input("Type your message:", key="user_input")
        if st.button("Send", key="user_send"):
            if user_msg:
                chat_history.append({"role": "user", "message": user_msg, "time": timestamp()})
                save_chat(user_id, chat_history)
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
        if user_list:
            # Show red dot for unread messages
            unread_users = []
            for uid in user_list:
                chat = load_chat(uid)
                if chat and chat[-1]["role"] == "user":
                    unread_users.append(uid)

            selected_user = st.selectbox(
                "Select a user:",
                [f"{u} 🔴" if u in unread_users else u for u in user_list]
            )
            selected_user = selected_user.replace(" 🔴", "")

            chat_history = load_chat(selected_user)

            st.markdown(f"### Chat with {selected_user}")
            last_admin_time = None
            for chat in chat_history:
                msg_time = chat.get("time", "")
                if chat["role"] == "user":
                    st.markdown(f"<div style='text-align:left; color:blue;'>🧑‍💻 User ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
                elif chat["role"] == "admin":
                    last_admin_time = datetime.strptime(msg_time, "%Y-%m-%d %H:%M:%S")
                    st.markdown(f"<div style='text-align:right; color:green;'>👨‍💼 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
                else:  # AI bot
                    st.markdown(f"<div style='text-align:right; color:purple;'>🤖 Bot ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

                # Show file download if exists
                if "file" in chat:
                    with open(chat["file"], "rb") as f:
                        st.download_button("⬇️ Download " + os.path.basename(chat["file"]), f, file_name=os.path.basename(chat["file"]))

            # Check if AI bot should auto-reply
            if chat_history:
                last_msg = chat_history[-1]
                if last_msg["role"] == "user":
                    last_time = datetime.strptime(last_msg["time"], "%Y-%m-%d %H:%M:%S")
                    if (datetime.now() - last_time).seconds > 180:  # 3 min
                        bot_msg = ai_bot_reply(chat_history)
                        chat_history.append({"role": "bot", "message": bot_msg, "time": timestamp()})
                        save_chat(selected_user, chat_history)

            # File Upload (Admin side)
            admin_file = st.file_uploader("Upload a file", key="admin_file")
            if admin_file:
                file_path = os.path.join(CHAT_DIR, f"{selected_user}_{admin_file.name}")
                with open(file_path, "wb") as f:
                    f.write(admin_file.getbuffer())
                chat_history.append({"role": "admin", "message": f"[📂 File: {admin_file.name}]", "file": file_path, "time": timestamp()})
                save_chat(selected_user, chat_history)
                st.success("✅ File sent!")
                st.rerun()

            # Reply box
            admin_reply = st.text_input("Your Reply:", key="admin_reply")
            if st.button("Send Reply"):
                if admin_reply:
                    chat_history.append({"role": "admin", "message": admin_reply, "time": timestamp()})
                    save_chat(selected_user, chat_history)
                    st.rerun()

            # Delete chat option
            if st.button("🗑️ Delete Chat"):
                os.remove(get_chat_path(selected_user))
                st.success("Chat deleted.")
                st.rerun()
        else:
            st.info("No users have started a chat yet.")
