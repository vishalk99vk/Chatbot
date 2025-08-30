import streamlit as st
import os
import json
import time
from datetime import datetime, timedelta
from openai import OpenAI

# --- CONFIG ---
CHAT_DIR = "chats"
ADMIN_PASSWORD = "Vishal@12345"   # change this
if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

# 🔑 Load OpenAI API Key (set in Streamlit secrets or env variable)
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY")))


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

def ai_bot_reply(user_message):
    """Generate AI response using OpenAI API"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant responding on behalf of Admin."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=100
        )
        return "🤖 Bot: " + response.choices[0].message.content.strip()
    except Exception as e:
        return "🤖 Bot: Sorry, I'm having trouble generating a response right now."


# --- Streamlit App ---
st.set_page_config(page_title="Live Chat", layout="wide")
st.title("💬 Live Chat System (User ↔ Admin + AI Bot Fallback)")

menu = st.sidebar.radio("Login as:", ["User", "Admin"])

# Auto-refresh every 2 seconds for live effect
st_autorefresh = st.sidebar.checkbox("🔄 Auto-refresh every 2s", value=True)
if st_autorefresh:
    st.experimental_autorefresh(interval=2000, key="refresh")


# --- User Section ---
if menu == "User":
    user_id = st.text_input("Enter your User ID (any unique name):")
    password = st.text_input("Set/Enter Password:", type="password")

    if user_id and password:
        chat_history = load_chat(user_id)

        # Save password if new user
        if not chat_history:
            chat_history.append({"role": "system", "message": f"USER_PASSWORD:{password}", "time": timestamp()})
            save_chat(user_id, chat_history)

        # Verify password
        stored_pwd = None
        for entry in chat_history:
            if entry["role"] == "system" and entry["message"].startswith("USER_PASSWORD:"):
                stored_pwd = entry["message"].split(":")[1]
                break

        if stored_pwd != password:
            st.error("❌ Wrong password")
        else:
            st.markdown("### Chat Window")
            for chat in chat_history:
                if chat["role"] == "system":  # skip system messages
                    continue
                msg_time = chat.get("time", "")
                if chat["role"] == "user":
                    st.markdown(f"<div style='text-align:right; color:blue;'>🧑‍💻 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:left; color:green;'>{chat['message']} ({msg_time})</div>", unsafe_allow_html=True)

            # File upload
            uploaded_file = st.file_uploader("📂 Upload a file", type=["jpg", "png", "pdf", "txt"])
            if uploaded_file:
                file_path = os.path.join(CHAT_DIR, f"{user_id}_{uploaded_file.name}")
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                chat_history.append({"role": "user", "message": f"📎 Uploaded file: {uploaded_file.name}", "time": timestamp()})
                save_chat(user_id, chat_history)
                st.success(f"File {uploaded_file.name} uploaded!")

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

            # --- AI BOT AUTOREPLY (if no admin response in 30s) ---
            if chat_history:
                last_msg = chat_history[-1]
                msg_time = datetime.strptime(last_msg["time"], "%Y-%m-%d %H:%M:%S")

                if last_msg["role"] == "user":
                    if datetime.now() - msg_time > timedelta(seconds=30):
                        # Auto AI bot reply
                        bot_response = ai_bot_reply(last_msg["message"])
                        chat_history.append({
                            "role": "admin",
                            "message": bot_response,
                            "time": timestamp()
                        })
                        save_chat(selected_user, chat_history)

            st.markdown(f"### Chat with {selected_user}")
            for chat in chat_history:
                if chat["role"] == "system":
                    continue
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

            # Delete chat option
            if st.button("🗑️ Delete this user's chat"):
                os.remove(get_chat_path(selected_user))
                st.success("Chat deleted.")
                st.rerun()

        else:
            st.info("No users have started a chat yet.")
