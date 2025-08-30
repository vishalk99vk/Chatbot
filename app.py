import streamlit as st
import os
import json
import time
import base64

# --- Config ---
CHAT_DIR = "chats"
USER_DB = "users.json"
ADMIN_PASSWORD = "admin123"  # Change this
AI_REPLY = "🤖 Auto-reply: Admin will get back to you shortly!"

if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

if not os.path.exists(USER_DB):
    with open(USER_DB, "w") as f:
        json.dump({}, f)


# --- Helpers ---
def get_chat_path(user_id):
    return os.path.join(CHAT_DIR, f"{user_id}.json")


def load_chat(user_id):
    path = get_chat_path(user_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"history": [], "last_read_user": 0, "last_read_admin": 0}


def save_chat(user_id, chat_data):
    path = get_chat_path(user_id)
    with open(path, "w") as f:
        json.dump(chat_data, f, indent=2)


def get_all_users():
    return [f.replace(".json", "") for f in os.listdir(CHAT_DIR) if f.endswith(".json")]


def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def load_users():
    with open(USER_DB, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=2)


def add_ai_reply_if_needed(user_id, chat_data):
    # If last user msg >3 mins ago and no admin reply after that
    if not chat_data["history"]:
        return chat_data
    last_msg = chat_data["history"][-1]
    if last_msg["role"] == "user":
        msg_time = time.mktime(time.strptime(last_msg["time"], "%Y-%m-%d %H:%M:%S"))
        if time.time() - msg_time > 180:  # 3 minutes
            chat_data["history"].append(
                {"role": "admin", "message": AI_REPLY, "time": timestamp()}
            )
    return chat_data


def render_file_download(file_data, filename):
    b64 = base64.b64encode(file_data).decode()
    href = f'<a href="data:file/octet-stream;base64,{b64}" download="{filename}">📥 {filename}</a>'
    st.markdown(href, unsafe_allow_html=True)


# --- Streamlit UI ---
st.set_page_config(page_title="Live Chat", layout="wide")

tab1, tab2 = st.tabs(["👤 User", "🛠️ Admin"])

st.sidebar.checkbox("🔄 Auto-refresh (2s)", value=True, key="autorefresh")
if st.session_state.autorefresh:
    st.sidebar.write("Auto-refresh enabled")
    st.experimental_autorefresh(interval=2000, key="refresh")


# --- User Tab ---
with tab1:
    st.header("👤 User Portal")

    users = load_users()
    mode = st.radio("Choose Action", ["Login", "Register"])

    if mode == "Register":
        new_user = st.text_input("Choose a User ID:")
        new_pwd = st.text_input("Choose Password:", type="password")
        if st.button("Register"):
            if new_user in users:
                st.error("User already exists!")
            else:
                users[new_user] = new_pwd
                save_users(users)
                st.success("✅ Registered! Now login.")

    elif mode == "Login":
        user_id = st.text_input("User ID:")
        pwd = st.text_input("Password:", type="password")
        if st.button("Login", key="user_login"):
            if user_id in users and users[user_id] == pwd:
                st.session_state.user_logged_in = user_id
                st.success(f"✅ Logged in as {user_id}")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    if "user_logged_in" in st.session_state:
        user_id = st.session_state.user_logged_in
        chat_data = load_chat(user_id)

        # Show unread counter
        unread = len(chat_data["history"]) - chat_data["last_read_user"]
        st.subheader(f"💬 Chat Window {'🔴 ('+str(unread)+')' if unread>0 else ''}")

        # Mark as read
        chat_data["last_read_user"] = len(chat_data["history"])
        save_chat(user_id, chat_data)

        for chat in chat_data["history"]:
            msg_time = chat.get("time", "")
            if chat["role"] == "user":
                st.markdown(f"<div style='text-align:right; color:blue;'>🧑‍💻 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:left; color:green;'>👨‍💼 Admin ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

            # Show download if file
            if chat.get("file"):
                render_file_download(base64.b64decode(chat["file"]), chat["filename"])

        user_msg = st.text_input("Type your message:", key="user_input")
        user_file = st.file_uploader("Attach file (optional):", key="user_file")
        if st.button("Send", key="user_send"):
            if user_msg or user_file:
                entry = {"role": "user", "message": user_msg, "time": timestamp()}
                if user_file:
                    entry["file"] = base64.b64encode(user_file.read()).decode()
                    entry["filename"] = user_file.name
                chat_data["history"].append(entry)
                save_chat(user_id, chat_data)
                st.rerun()


# --- Admin Tab ---
with tab2:
    st.header("🛠️ Admin Portal")

    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        pwd = st.text_input("Enter Admin Password:", type="password")
        if st.button("Login as Admin"):
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
            # Show unread counts
            annotated_users = []
            for u in user_list:
                chat_data = load_chat(u)
                unread_admin = len(chat_data["history"]) - chat_data["last_read_admin"]
                if unread_admin > 0:
                    annotated_users.append(f"{u} 🔴 ({unread_admin})")
                else:
                    annotated_users.append(u)

            selected_label = st.selectbox("Select a user:", annotated_users)
            selected_user = selected_label.split(" ")[0]  # remove 🔴 part
            chat_data = load_chat(selected_user)
            chat_data = add_ai_reply_if_needed(selected_user, chat_data)

            st.markdown(f"### Chat with {selected_user}")

            # Mark as read
            chat_data["last_read_admin"] = len(chat_data["history"])
            save_chat(selected_user, chat_data)

            for chat in chat_data["history"]:
                msg_time = chat.get("time", "")
                if chat["role"] == "user":
                    st.markdown(f"<div style='text-align:left; color:blue;'>🧑‍💻 User ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:right; color:green;'>👨‍💼 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

                if chat.get("file"):
                    render_file_download(base64.b64decode(chat["file"]), chat["filename"])

            admin_msg = st.text_input("Your Reply:", key="admin_reply")
            admin_file = st.file_uploader("Attach file (optional):", key="admin_file")
            if st.button("Send Reply"):
                if admin_msg or admin_file:
                    entry = {"role": "admin", "message": admin_msg, "time": timestamp()}
                    if admin_file:
                        entry["file"] = base64.b64encode(admin_file.read()).decode()
                        entry["filename"] = admin_file.name
                    chat_data["history"].append(entry)
                    save_chat(selected_user, chat_data)
                    st.rerun()

            # Delete chat option
            if st.button("🗑️ Delete Chat"):
                os.remove(get_chat_path(selected_user))
                st.success("Chat deleted")
                st.rerun()

        else:
            st.info("No users have started a chat yet.")
