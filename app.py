import streamlit as st
import os
import json
from datetime import datetime, timedelta

# File to store chat history
CHAT_FILE = "chat_history.json"

# Load chat history
if os.path.exists(CHAT_FILE):
    with open(CHAT_FILE, "r") as f:
        chat_history = json.load(f)
else:
    chat_history = []

# Save chat history
def save_chat():
    with open(CHAT_FILE, "w") as f:
        json.dump(chat_history, f)

# Auto AI reply if admin is silent for >3 mins
def auto_ai_reply():
    global chat_history
    if chat_history:
        last_admin_msg = max([c for c in chat_history if c["role"] == "admin"], default=None)
        last_msg = chat_history[-1]

        if last_msg["role"] == "user":
            last_time = datetime.strptime(last_msg["time"], "%Y-%m-%d %H:%M:%S")
            if datetime.now() - last_time > timedelta(minutes=3):
                if not last_admin_msg or datetime.strptime(last_admin_msg["time"], "%Y-%m-%d %H:%M:%S") < last_time:
                    ai_reply = {
                        "role": "admin",
                        "message": "🤖 Auto-reply: Admin will respond shortly.",
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    chat_history.append(ai_reply)
                    save_chat()

# Streamlit UI
st.set_page_config("Chat App", layout="wide")

st.title("💬 Secure Chat App with File Sharing")

# Tabs for Login/Register
tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

# Dummy user DB
if "users" not in st.session_state:
    st.session_state.users = {"admin": "admin123"}

if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None

with tab2:
    st.subheader("Register")
    new_user = st.text_input("Choose username")
    new_pass = st.text_input("Choose password", type="password")
    if st.button("Register"):
        if new_user in st.session_state.users:
            st.warning("Username already exists!")
        else:
            st.session_state.users[new_user] = new_pass
            st.success("Registration successful! Now login.")

with tab1:
    st.subheader("Login")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if user in st.session_state.users and st.session_state.users[user] == pw:
            st.session_state.username = user
            st.session_state.role = "admin" if user == "admin" else "user"
            st.success(f"Welcome {user} ({st.session_state.role})")
        else:
            st.error("Invalid credentials!")

# Only logged in users can chat
if st.session_state.role:
    st.experimental_set_query_params(refresh="true")  # ✅ Auto-refresh

    auto_ai_reply()  # check AI reply need

    st.subheader("Chat Window")

    # Show chat history with bubbles + file handling
    for idx, chat in enumerate(chat_history):
        msg_time = chat.get("time", "")
        role = chat["role"]
        msg = chat["message"]

        # User view
        if st.session_state.role == "user":
            if role == "user":
                st.markdown(
                    f"<div style='text-align:right; background:#DCF8C6; padding:8px; border-radius:10px; margin:5px; display:inline-block;'>🧑‍💻 You ({msg_time}): {msg}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='text-align:left; background:#E8EAF6; padding:8px; border-radius:10px; margin:5px; display:inline-block;'>👨‍💼 Admin ({msg_time}): {msg}</div>",
                    unsafe_allow_html=True
                )

        # Admin view
        elif st.session_state.role == "admin":
            if role == "admin":
                st.markdown(
                    f"<div style='text-align:right; background:#C8E6C9; padding:8px; border-radius:10px; margin:5px; display:inline-block;'>👨‍💼 You ({msg_time}): {msg}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='text-align:left; background:#BBDEFB; padding:8px; border-radius:10px; margin:5px; display:inline-block;'>🧑‍💻 User ({msg_time}): {msg}</div>",
                    unsafe_allow_html=True
                )

        # ✅ File download if exists
        if "file" in chat and os.path.exists(chat["file"]):
            file_path = chat["file"]
            file_name = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                st.download_button(
                    label=f"⬇️ Download {file_name}",
                    data=f,
                    file_name=file_name,
                    mime="application/octet-stream"
                )

        # ✅ Admin delete option
        if st.session_state.role == "admin":
            if st.button(f"🗑 Delete Msg {idx}", key=f"del{idx}"):
                chat_history.pop(idx)
                save_chat()
                st.experimental_rerun()

    # Input section
    st.subheader("Send Message")
    msg = st.text_area("Type your message")
    file_upload = st.file_uploader("Attach a file", type=None)

    if st.button("Send"):
        entry = {
            "role": st.session_state.role,
            "message": msg,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        if file_upload:
            save_path = os.path.join("uploads", file_upload.name)
            os.makedirs("uploads", exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(file_upload.getbuffer())
            entry["file"] = save_path

        chat_history.append(entry)
        save_chat()
        st.experimental_rerun()
