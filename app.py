import streamlit as st
import os
import json
import datetime
from streamlit_autorefresh import st_autorefresh

# ----------------- CONFIG -----------------
USERS_FILE = "users.json"
CHAT_FILE = "chat.json"
ADMIN_USERNAME = "admin"

# Ensure data files exist
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(CHAT_FILE):
    with open(CHAT_FILE, "w") as f:
        json.dump({}, f)

# ----------------- HELPERS -----------------
def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_chat():
    with open(CHAT_FILE, "r") as f:
        return json.load(f)

def save_chat(chat):
    with open(CHAT_FILE, "w") as f:
        json.dump(chat, f, indent=2)

def get_time():
    return datetime.datetime.now().strftime("%H:%M:%S")

# ----------------- AUTO REFRESH -----------------
st_autorefresh(interval=2000, key="refresh")  # 2 sec refresh

# ----------------- LOGIN / REGISTER -----------------
st.title("🔐 Chat App")

tab1, tab2 = st.tabs(["Login", "Register"])

with tab2:
    st.subheader("Register")
    new_user = st.text_input("Username", key="reg_user")
    new_pass = st.text_input("Password", type="password", key="reg_pass")
    if st.button("Register"):
        users = load_users()
        if new_user in users:
            st.warning("Username already exists!")
        else:
            users[new_user] = {"password": new_pass}
            save_users(users)
            st.success("Registration successful! Please login.")

with tab1:
    st.subheader("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        users = load_users()
        if username in users and users[username]["password"] == password:
            st.session_state["username"] = username
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

# ----------------- MAIN APP -----------------
if "username" in st.session_state:
    user = st.session_state["username"]
    st.sidebar.success(f"✅ Logged in as {user}")
    chat_data = load_chat()

    # Ensure user chat exists
    if user != ADMIN_USERNAME and user not in chat_data:
        chat_data[user] = {"messages": [], "last_read_admin": 0, "last_read_user": 0}
        save_chat(chat_data)

    # ----------------- ADMIN PANEL -----------------
    if user == ADMIN_USERNAME:
        st.header("👨‍💼 Admin Dashboard")

        if chat_data:
            user_list = []
            for uname, ch in chat_data.items():
                unread = len(ch["messages"]) - ch["last_read_admin"]
                badge = f" 🔴({unread})" if unread > 0 else ""
                user_list.append(f"{uname}{badge}")

            selected = st.selectbox("Select user", user_list)
            selected_user = selected.split("🔴")[0].strip()
            st.subheader(f"Chat with {selected_user}")

            chat_history = chat_data[selected_user]["messages"]
            for idx, chat in enumerate(chat_history):
                msg_time = chat.get("time", "")
                if chat["role"] == "user":
                    st.markdown(f"<div style='text-align:left; color:blue;'>🧑‍💻 {selected_user} ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:right; color:green;'>👨‍💼 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

                # ✅ File download handling
                if "file" in chat and os.path.exists(chat["file"]):
                    file_path = chat["file"]
                    file_name = os.path.basename(file_path)
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Download {file_name}",
                            data=f,
                            file_name=file_name,
                            mime="application/octet-stream",
                            key=f"dl_admin_{idx}"
                        )

            # Mark all messages read for admin
            chat_data[selected_user]["last_read_admin"] = len(chat_history)
            save_chat(chat_data)

            msg = st.text_input("Type your message")
            file_upload = st.file_uploader("Upload a file", key="admin_file")

            if st.button("Send", key="send_admin"):
                file_path = None
                if file_upload:
                    file_path = os.path.join("uploads", file_upload.name)
                    os.makedirs("uploads", exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(file_upload.read())

                chat_history.append({
                    "role": "admin",
                    "message": msg,
                    "time": get_time(),
                    "file": file_path
                })
                save_chat(chat_data)
                st.experimental_rerun()

            # Delete chat option
            if st.button("❌ Delete Chat"):
                del chat_data[selected_user]
                save_chat(chat_data)
                st.experimental_rerun()

    # ----------------- USER PANEL -----------------
    else:
        st.header("💬 Chat Window")

        chat_history = chat_data[user]["messages"]
        unread = len(chat_history) - chat_data[user]["last_read_user"]
        if unread > 0:
            st.subheader(f"🔴 You have {unread} unread message(s)")

        for idx, chat in enumerate(chat_history):
            msg_time = chat.get("time", "")
            if chat["role"] == "user":
                st.markdown(f"<div style='text-align:right; color:blue;'>🧑‍💻 You ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:left; color:green;'>👨‍💼 Admin ({msg_time}): {chat['message']}</div>", unsafe_allow_html=True)

            # ✅ File download handling
            if "file" in chat and os.path.exists(chat["file"]):
                file_path = chat["file"]
                file_name = os.path.basename(file_path)
                with open(file_path, "rb") as f:
                    st.download_button(
                        label=f"⬇️ Download {file_name}",
                        data=f,
                        file_name=file_name,
                        mime="application/octet-stream",
                        key=f"dl_user_{idx}"
                    )

        # Mark all as read for user
        chat_data[user]["last_read_user"] = len(chat_history)
        save_chat(chat_data)

        msg = st.text_input("Type your message")
        file_upload = st.file_uploader("Upload a file", key="user_file")

        if st.button("Send", key="send_user"):
            file_path = None
            if file_upload:
                file_path = os.path.join("uploads", file_upload.name)
                os.makedirs("uploads", exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(file_upload.read())

            chat_history.append({
                "role": "user",
                "message": msg,
                "time": get_time(),
                "file": file_path
            })
            save_chat(chat_data)
            st.experimental_rerun()
