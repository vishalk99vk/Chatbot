import streamlit as st
import os
import json
import time
import openai

# ---------------- CONFIG ----------------
CHAT_DIR = "chats"
USER_DIR = "users"
ADMIN_PASSWORD = "admin123"  # Change this
BOT_DELAY = 30  # seconds

# OpenAI API key (make sure to set in Streamlit Secrets or env vars)
openai.api_key = os.getenv("OPENAI_API_KEY")

if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)
if not os.path.exists(USER_DIR):
    os.makedirs(USER_DIR)

# ---------------- HELPERS ----------------
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

def user_path(user_id):
    return os.path.join(USER_DIR, f"{user_id}.json")

def register_user(user_id, password):
    path = user_path(user_id)
    if os.path.exists(path):
        return False
    with open(path, "w") as f:
        json.dump({"password": password}, f)
    return True

def validate_user(user_id, password):
    path = user_path(user_id)
    if not os.path.exists(path):
        return False
    with open(path, "r") as f:
        data = json.load(f)
        return data.get("password") == password

def ai_bot_reply(user_message, chat_history):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or gpt-4o-mini if enabled
            messages=[
                {"role": "system", "content": "You are an AI assistant replying temporarily on behalf of the admin. Keep responses short, professional, and helpful."},
                *[{"role": m["role"], "content": m["message"]} for m in chat_history],
                {"role": "user", "content": user_message}
            ],
            max_tokens=150
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return "⚠️ AI bot is currently unavailable."

# ---------------- STREAMLIT APP ----------------
st.set_page_config(page_title="Live Chat", layout="wide")
st.title("💬 Live Chat System (User ↔ Admin + AI Backup)")

menu = st.sidebar.radio("Login as:", ["User", "Admin"])

# Auto-refresh
st_autorefresh = st.sidebar.checkbox("🔄 Auto-refresh every 2s", value=True)
if st_autorefresh:
    st.experimental_autorefresh(interval=2000, key="refresh")

# ---------------- USER SECTION ----------------
if menu == "User":
    action = st.radio("Choose:", ["Login", "Register"])
    user_id = st.text_input("User ID:")

    if action == "Register":
        pwd = st.text_input("Set Password:", type="password")
        if st.button("Register"):
            if register_user(user_id, pwd):
                st.success("✅ Registered successfully! Now login.")
            else:
                st.error("❌ User already exists.")

    elif action == "Login":
        pwd = st.text_input("Password:", type="password")
        if st.button("Login"):
            if validate_user(user_id, pwd):
                st.session_state["user_authenticated"] = True
                st.session_state["current_user"] = user_id
                st.success("✅ Logged in successfully")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    if st.session_state.get("user_authenticated") and st.session_state.get("current_user") == user_id:
        chat_history = load_chat(user_id)

        st.markdown("### Chat Window")
        for chat in chat_history:
            msg_time = chat.get("time", "")
            if chat["role"] == "user":
                st.markdown(f"<div style='text-align:right; color:blue;'>🧑‍💻 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
            elif chat["role"] == "admin":
                st.markdown(f"<div style='text-align:left; color:green;'>👨‍💼 Admin ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
            elif chat["role"] == "bot":
                st.markdown(f"<div style='text-align:left; color:orange;'>🤖 AI Bot ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

        # Send message
        user_msg = st.text_input("Type your message:", key="user_input")
        if st.button("Send", key="user_send"):
            if user_msg:
                chat_history.append({"role": "user", "message": user_msg, "time": timestamp()})
                save_chat(user_id, chat_history)
                st.rerun()

        # File upload
        uploaded_file = st.file_uploader("Upload a file")
        if uploaded_file:
            file_path = os.path.join(CHAT_DIR, f"{user_id}_{uploaded_file.name}")
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"File {uploaded_file.name} uploaded.")
            st.download_button("📥 Download file", data=uploaded_file.getvalue(), file_name=uploaded_file.name)


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
            last_user_msg, last_time = None, None
            last_admin_time = None

            for chat in chat_history:
                msg_time = chat.get("time", "")
                if chat["role"] == "user":
                    st.markdown(f"<div style='text-align:left; color:blue;'>🧑‍💻 User ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
                    last_user_msg, last_time = chat["message"], chat["time"]
                elif chat["role"] == "admin":
                    st.markdown(f"<div style='text-align:right; color:green;'>👨‍💼 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
                    last_admin_time = chat["time"]
                elif chat["role"] == "bot":
                    st.markdown(f"<div style='text-align:left; color:orange;'>🤖 AI Bot ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

            # Auto bot response if admin idle
            if last_user_msg:
                last_msg_time_struct = time.strptime(last_time, "%Y-%m-%d %H:%M:%S")
                last_msg_epoch = time.mktime(last_msg_time_struct)

                if not last_admin_time or time.mktime(time.strptime(last_admin_time, "%Y-%m-%d %H:%M:%S")) < last_msg_epoch:
                    if time.time() - last_msg_epoch > BOT_DELAY:
                        ai_reply = ai_bot_reply(last_user_msg, chat_history)
                        chat_history.append({"role": "bot", "message": ai_reply, "time": timestamp()})
                        save_chat(selected_user, chat_history)
                        st.rerun()

            # Reply box
            admin_reply = st.text_input("Your Reply:", key="admin_reply")
            if st.button("Send Reply"):
                if admin_reply:
                    chat_history.append({"role": "admin", "message": admin_reply, "time": timestamp()})
                    save_chat(selected_user, chat_history)
                    st.rerun()

            # Delete chat
            if st.button("🗑️ Delete Chat"):
                os.remove(get_chat_path(selected_user))
                st.success("Chat deleted.")
                st.rerun()
        else:
            st.info("No users have started a chat yet.")
