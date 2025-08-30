import streamlit as st
import os
import json
import time
from datetime import datetime, timedelta

# ------------------ CONFIG ------------------
CHAT_DIR = "chats"
ADMIN_PASSWORD = "Vishal@12345"  # Change this
USER_DB = "users.json"       # Stores user credentials

if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

# ------------------ HELPERS ------------------
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

def delete_chat(user_id):
    path = get_chat_path(user_id)
    if os.path.exists(path):
        os.remove(path)

def get_all_users():
    return [f.replace(".json", "") for f in os.listdir(CHAT_DIR) if f.endswith(".json")]

def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=2)

# ------------------ AI BOT ------------------
def ai_bot_reply(user_message):
    """Simple rule-based bot response (replace with OpenAI if needed)"""
    if "price" in user_message.lower():
        return "🤖 Bot: Our pricing details will be shared soon by the Admin."
    elif "hello" in user_message.lower():
        return "🤖 Bot: Hello! Thanks for reaching out. The Admin will reply shortly."
    else:
        return "🤖 Bot: Thanks for your message! The Admin will respond as soon as possible."

# ------------------ STREAMLIT APP ------------------
st.set_page_config(page_title="Live Chat", layout="wide")
st.title("💬 Live Chat System (User ↔ Admin + AI Bot)")

menu = st.sidebar.radio("Login as:", ["User", "Admin"])

st_autorefresh = st.sidebar.checkbox("🔄 Auto-refresh every 2s", value=True)
if st_autorefresh:
    st.experimental_autorefresh(interval=2000, key="refresh")

# ------------------ USER SECTION ------------------
if menu == "User":
    users = load_users()
    action = st.radio("Choose action:", ["Login", "Register"])

    if action == "Register":
        new_user = st.text_input("Choose User ID:")
        new_pass = st.text_input("Choose Password:", type="password")
        if st.button("Register"):
            if new_user in users:
                st.error("User already exists!")
            else:
                users[new_user] = new_pass
                save_users(users)
                st.success("✅ Registered successfully! Please login.")

    elif action == "Login":
        user_id = st.text_input("User ID:")
        user_pass = st.text_input("Password:", type="password")
        if st.button("Login"):
            if user_id in users and users[user_id] == user_pass:
                st.session_state["user_authenticated"] = True
                st.session_state["user_id"] = user_id
                st.success("✅ Logged in successfully")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    if st.session_state.get("user_authenticated", False):
        user_id = st.session_state["user_id"]
        chat_history = load_chat(user_id)

        st.markdown("### Chat Window")
        for chat in chat_history:
            msg_time = chat.get("time", "")
            if chat["role"] == "user":
                st.markdown(f"<div style='text-align:right; color:blue;'>🧑‍💻 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:left; color:green;'>👨‍💼 Admin ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

            # Show file download if exists
            if "file" in chat:
                with open(chat["file"], "rb") as f:
                    st.download_button("📥 Download File", f, file_name=os.path.basename(chat["file"]))

        # Send message
        user_msg = st.text_input("Type your message:", key="user_input")
        if st.button("Send", key="user_send"):
            if user_msg:
                chat_history.append({"role": "user", "message": user_msg, "time": timestamp()})
                save_chat(user_id, chat_history)
                st.rerun()

        # File upload
        uploaded_file = st.file_uploader("Upload a file")
        if uploaded_file is not None:
            save_path = os.path.join(CHAT_DIR, f"{user_id}_{uploaded_file.name}")
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            chat_history.append({"role": "user", "message": f"📎 Sent a file: {uploaded_file.name}", "time": timestamp(), "file": save_path})
            save_chat(user_id, chat_history)
            st.success("✅ File uploaded")
            st.rerun()

# ------------------ ADMIN SECTION ------------------
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
                else:
                    st.markdown(f"<div style='text-align:right; color:green;'>👨‍💼 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

                # Show file download if exists
                if "file" in chat:
                    with open(chat["file"], "rb") as f:
                        st.download_button("📥 Download File", f, file_name=os.path.basename(chat["file"]))

            # Auto bot check
            if chat_history:
                last_msg = chat_history[-1]
                msg_time = datetime.strptime(last_msg["time"], "%Y-%m-%d %H:%M:%S")
                if last_msg["role"] == "user" and datetime.now() - msg_time > timedelta(minutes=3):
                    bot_response = ai_bot_reply(last_msg["message"])
                    chat_history.append({"role": "admin", "message": bot_response, "time": timestamp()})
                    save_chat(selected_user, chat_history)
                    st.info("🤖 Bot replied automatically")

            # Reply box
            admin_reply = st.text_input("Your Reply:", key="admin_reply")
            if st.button("Send Reply"):
                if admin_reply:
                    chat_history.append({"role": "admin", "message": admin_reply, "time": timestamp()})
                    save_chat(selected_user, chat_history)
                    st.rerun()

            # File upload
            uploaded_file = st.file_uploader("Upload a file for user")
            if uploaded_file is not None:
                save_path = os.path.join(CHAT_DIR, f"{selected_user}_{uploaded_file.name}")
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                chat_history.append({"role": "admin", "message": f"📎 Sent a file: {uploaded_file.name}", "time": timestamp(), "file": save_path})
                save_chat(selected_user, chat_history)
                st.success("✅ File uploaded to user")
                st.rerun()

            # Delete chat
            if st.button("🗑️ Delete Chat with this User"):
                delete_chat(selected_user)
                st.warning(f"Deleted chat with {selected_user}")
                st.rerun()

        else:
            st.info("No users have started a chat yet.")
