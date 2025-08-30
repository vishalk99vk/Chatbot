import streamlit as st
import time
import threading

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Secure Chat App", layout="wide")
ADMIN_PASS = "12345"  # Change this for security

# ----------------------------
# INIT SESSION STATE
# ----------------------------
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "files" not in st.session_state:
    st.session_state.files = []
if "chat_running" not in st.session_state:
    st.session_state.chat_running = False


# ----------------------------
# CHAT UPDATER (runs in thread)
# ----------------------------
def chat_updater(placeholder):
    while st.session_state.chat_running:
        with placeholder.container():
            st.subheader("💬 Chat Messages (auto-updating)")
            for sender, msg, uname in st.session_state.messages:
                if sender == "User":
                    st.markdown(f"🧑 **{uname}:** {msg}")
                else:
                    st.markdown(f"👨‍💻 **Admin:** {msg}")
        time.sleep(1)


# ----------------------------
# LOGIN PANEL
# ----------------------------
if st.session_state.role is None:
    st.title("🔐 Login Panel")

    role = st.radio("Who are you?", ["User", "Admin"])

    if role == "Admin":
        admin_password = st.text_input("Enter Admin Password:", type="password")
        if st.button("Proceed as Admin"):
            if admin_password == ADMIN_PASS:
                st.session_state.role = "Admin"
                st.success("✅ Logged in as Admin!")
                st.rerun()
            else:
                st.error("❌ Incorrect password")

    else:  # User login
        username = st.text_input("Enter your name:")
        if st.button("Proceed as User"):
            if username.strip():
                st.session_state.role = "User"
                st.session_state.username = username.strip()
                st.success(f"✅ Logged in as User: {username}")
                st.rerun()
            else:
                st.warning("⚠️ Please enter your name before continuing.")

    st.stop()


# ----------------------------
# CHAT AREA (ONLY REFRESHES)
# ----------------------------
chat_placeholder = st.empty()

if not st.session_state.chat_running:
    st.session_state.chat_running = True
    thread = threading.Thread(target=chat_updater, args=(chat_placeholder,), daemon=True)
    thread.start()


# ----------------------------
# USER PANEL
# ----------------------------
if st.session_state.role == "User":
    st.title(f"🧑 User Panel - Welcome {st.session_state.username}")

    user_msg = st.text_input("Type your message:")
    if st.button("Send", key="user_send") and user_msg:
        st.session_state.messages.append(("User", user_msg, st.session_state.username))

    uploaded_file = st.file_uploader("📂 Upload a file")  # no type filter
    if uploaded_file:
        size_mb = uploaded_file.size / (1024 * 1024)
        if size_mb > 200:
            st.warning("⚠️ Please upload this file on Google Drive and share the link instead.")
        else:
            st.session_state.files.append((st.session_state.username, uploaded_file.name))
            st.success(f"✅ Uploaded: {uploaded_file.name}")

    if st.button("Logout"):
        st.session_state.chat_running = False
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()


# ----------------------------
# ADMIN PANEL
# ----------------------------
elif st.session_state.role == "Admin":
    st.title("🛡️ Admin Panel")

    admin_msg = st.text_input("Reply to User:")
    if st.button("Send", key="admin_send") and admin_msg:
        st.session_state.messages.append(("Admin", admin_msg, None))

    st.subheader("📂 Uploaded Files")
    for uname, fname in st.session_state.files:
        st.markdown(f"📄 From **{uname}**: {fname}")

    if st.button("Logout"):
        st.session_state.chat_running = False
        st.session_state.role = None
        st.rerun()
