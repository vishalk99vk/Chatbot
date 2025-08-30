import streamlit as st
import os
import json
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

CHAT_DIR = "chats"
USER_FILE = "users.json"
ADMIN_PASSWORD = "Vishal@12345"  # change this
AI_BOT_NAME = "🤖 AutoBot"

if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)


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


def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)


def last_admin_message_time(chat_history):
    for chat in reversed(chat_history):
        if chat["role"] == "admin":
            return datetime.strptime(chat["time"], "%Y-%m-%d %H:%M:%S")
    return None


# --- Streamlit App ---
st.set_page_config(page_title="Live Chat", layout="wide")
st.title("💬 Live Chat System (User ↔ Admin + AI Bot)")

menu = st.sidebar.radio("Login as:", ["User", "Admin"])

# Auto-refresh every 2 seconds for live effect
st_autorefresh_enabled = st.sidebar.checkbox("🔄 Auto-refresh every 2s", value=True)
if st_autorefresh_enabled:
    st_autorefresh(interval=2000, key="refresh")

# --- User Section ---
if menu == "User":
    users = load_users()

    st.markdown("### 👤 User Login / Register")
    user_id = st.text_input("Enter User ID (any unique name):")
    password = st.text_input("Enter Password:", type="password")

    if user_id and password:
        if user_id not in users:
            if st.button("Register"):
                users[user_id] = password
                save_users(users)
                st.success("✅ Registered! Please log in again.")
                st.stop()
        else:
            if users[user_id] == password:
                chat_history = load_chat(user_id)

                st.markdown("### Chat Window")
                for chat in chat_history:
                    msg_time = chat.get("time", "")
                    if chat["role"] == "user":
                        if chat.get("file"):
                            st.markdown(
                                f"<div style='text-align:right; color:blue;'>🧑‍💻 You ({msg_time}): 📎 <a href='{chat['file']}' download>{os.path.basename(chat['file'])}</a></div>",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f"<div style='text-align:right; color:blue;'>🧑‍💻 You ({msg_time}): {chat['message']}</div>",
                                unsafe_allow_html=True,
                            )
                    elif chat["role"] == "admin":
                        st.markdown(
                            f"<div style='text-align:left; color:green;'>👨‍💼 Admin ({msg_time}): {chat['message']}</div>",
                            unsafe_allow_html=True,
                        )
                    elif chat["role"] == "bot":
                        st.markdown(
                            f"<div style='text-align:left; color:orange;'>{AI_BOT_NAME} ({msg_time}): {chat['message']}</div>",
                            unsafe_allow_html=True,
                        )

                user_msg = st.text_input("Type your message:", key="user_input")
                uploaded_file = st.file_uploader("Upload a file", key="user_file")

                if st.button("Send", key="user_send"):
                    if user_msg or uploaded_file:
                        msg = {"role": "user", "message": user_msg, "time": timestamp()}
                        if uploaded_file:
                            file_path = os.path.join(CHAT_DIR, uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            msg["file"] = file_path
                        chat_history.append(msg)
                        save_chat(user_id, chat_history)
                        st.rerun()
            else:
                st.error("❌ Wrong password!")

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

            # --- AI Bot Fallback ---
            if chat_history:
                last_admin = last_admin_message_time(chat_history)
                if last_admin:
                    diff = (datetime.now() - last_admin).total_seconds()
                    if diff > 180 and not any(msg["role"] == "bot" for msg in chat_history[-2:]):
                        chat_history.append({
                            "role": "bot",
                            "message": "I noticed admin hasn’t replied yet. How can I help you in the meantime?",
                            "time": timestamp()
                        })
                        save_chat(selected_user, chat_history)

            st.markdown(f"### Chat with {selected_user}")
            for chat in chat_history:
                msg_time = chat.get("time", "")
                if chat["role"] == "user":
                    if chat.get("file"):
                        st.markdown(
                            f"<div style='text-align:left; color:blue;'>🧑‍💻 User ({msg_time}): 📎 <a href='{chat['file']}' download>{os.path.basename(chat['file'])}</a></div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"<div style='text-align:left; color:blue;'>🧑‍💻 User ({msg_time}): {chat['message']}</div>",
                            unsafe_allow_html=True,
                        )
                elif chat["role"] == "admin":
                    st.markdown(
                        f"<div style='text-align:right; color:green;'>👨‍💼 You ({msg_time}): {chat['message']}</div>",
                        unsafe_allow_html=True,
                    )
                elif chat["role"] == "bot":
                    st.markdown(
                        f"<div style='text-align:left; color:orange;'>{AI_BOT_NAME} ({msg_time}): {chat['message']}</div>",
                        unsafe_allow_html=True,
                    )

            # Reply box
            admin_reply = st.text_input("Your Reply:", key="admin_reply")
            if st.button("Send Reply"):
                if admin_reply:
                    chat_history.append({"role": "admin", "message": admin_reply, "time": timestamp()})
                    save_chat(selected_user, chat_history)
                    st.rerun()

            # Delete chat
            if st.button("🗑️ Delete Chat with this User"):
                os.remove(get_chat_path(selected_user))
                st.success(f"Chat with {selected_user} deleted.")
                st.rerun()
        else:
            st.info("No users have started a chat yet.")
