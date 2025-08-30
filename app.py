import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Secure Chat App", layout="wide")
ADMIN_PASS = "12345"  # Change to strong password or store in st.secrets

# ----------------------------
# INIT SESSION STATE
# ----------------------------
if "role" not in st.session_state:
    st.session_state.role = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "files" not in st.session_state:
    st.session_state.files = []


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

    else:
        if st.button("Proceed as User"):
            st.session_state.role = "User"
            st.success("✅ Logged in as User!")
            st.rerun()

    st.stop()


# ----------------------------
# CHAT REFRESHABLE CONTAINER
# ----------------------------
chat_container = st.empty()

def render_chat():
    with chat_container.container():
        st.subheader("💬 Chat Messages")
        for sender, msg in st.session_state.messages:
            if sender == "User":
                st.markdown(f"🧑 **User:** {msg}")
            else:
                st.markdown(f"👨‍💻 **Admin:** {msg}")

# Refresh ONLY chat every 1 second
st_autorefresh(interval=1000, key="chat_refresh")
render_chat()


# ----------------------------
# USER PANEL
# ----------------------------
if st.session_state.role == "User":
    st.title("🧑 User Panel")

    user_msg = st.text_input("Type your message:")
    if st.button("Send", key="user_send") and user_msg:
        st.session_state.messages.append(("User", user_msg))
        st.rerun()

    uploaded_file = st.file_uploader("📂 Upload a file", type=None)
    if uploaded_file:
        size_mb = uploaded_file.size / (1024 * 1024)
        if size_mb > 200:
            st.warning("⚠️ Please upload this file on Google Drive and share the link instead.")
        else:
            st.session_state.files.append(("User", uploaded_file.name))
            st.success(f"✅ Uploaded: {uploaded_file.name}")

    if st.button("Logout"):
        st.session_state.role = None
        st.rerun()


# ----------------------------
# ADMIN PANEL
# ----------------------------
elif st.session_state.role == "Admin":
    st.title("🛡️ Admin Panel")

    admin_msg = st.text_input("Reply to User:")
    if st.button("Send", key="admin_send") and admin_msg:
        st.session_state.messages.append(("Admin", admin_msg))
        st.rerun()

    st.subheader("📂 Uploaded Files")
    for sender, fname in st.session_state.files:
        st.markdown(f"📄 From **{sender}**: {fname}")

    if st.button("Logout"):
        st.session_state.role = None
        st.rerun()
