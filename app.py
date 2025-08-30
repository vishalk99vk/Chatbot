import streamlit as st
import os
import json
import time

CHAT_DIR = "chats"
ADMIN_PASSWORD = "admin123"  # change this

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


# --- Streamlit App ---
st.set_page_config(page_title="Live Chat", layout="wide")
st.title("💬 Live Chat System (User ↔ Admin)")

menu = st.sidebar.radio("Login as:", ["User", "Admin"])

# Auto-refresh every 2 seconds for live effect
st_autorefresh = st.sidebar.checkbox("🔄 Auto-refresh every 2s", value=True)
if st_autorefresh:
    st.experimental_autorefresh(interval=2000, key="refresh")


# --- User Section ---
if menu == "User":
    user_id = st.text_input("Enter your User ID (any unique name):")
    if user_id:
        chat_history = load_chat(user_id)

        st.markdown("### Chat Window")
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
                else:
                    st.markdown(f"<div style='text-align:right; color:green;'>👨‍💼 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

            # Reply box
            admin_reply = st.text_input("Your Reply:", key="admin_reply")
            if st.button("Send Reply"):
                if admin_reply:
                    chat_history.append({"role": "admin", "message": admin_reply, "time": timestamp()})
                    save_chat(selected_user, chat_history)
                    st.rerun()
        else:
            st.info("No users have started a chat yet.")
