import streamlit as st
import time
import os

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Secure Chat App", layout="wide")
ADMIN_PASS = "12345"  # 🔐 Change to a strong password or use st.secrets

# ----------------------------
# AUTO REFRESH (every 1s)
# ----------------------------
time.sleep(1)
st.experimental_rerun()

# ----------------------------
# INIT SESSION STATE
# ----------------------------
if "role" not in st.session_state:
    st.session_state.role = None
if "messages" not in st.session_state:
    st.session_state.messages = []  # Store chat history
if "files" not in st.session_state:
    st.session_state.files = []  # Store uploaded files


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
                st.experimental_rerun()
            else:
                st.error("❌ Incorrect password")

    else:
        if st.button("Proceed as User"):
            st.session_state.role = "User"
            st.success("✅ Logged in as User!")
            st.experimental_rerun()

    st.stop()


# ----------------------------
# CHAT PANELS
# ----------------------------
def render_chat():
    """Render chat messages."""
    for sender, msg in st.session_state.messages:
        if sender == "User":
            st.markdown(f"🧑 **User:** {msg}")
        else:
            st.markdown(f"👨‍💻 **Admin:** {msg}")


# ----------------------------
# USER PANEL
# ----------------------------
if st.session_state.role == "User":
    st.title("💬 User Panel")

    render_chat()

    # Send message
    user_msg = st.text_input("Type your message:")
    if st.button("Send", key="user_send") and user_msg:
        st.session_state.messages.append(("User", user_msg))
        st.experimental_rerun()

    # Upload file
    uploaded_file = st.file_uploader("📂 Upload a file", type=None)
    if uploaded_file:
        size_mb = uploaded_file.size / (1024 * 1024)
        if size_mb > 200:
            st.warning("⚠️ Please upload this file on Google Drive and share the link instead.")
        else:
            st.session_state.files.append(("User", uploaded_file.name))
            st.success(f"✅ Uploaded: {uploaded_file.name}")

    # Logout
    if st.button("Logout"):
        st.session_state.role = None
        st.experimental_rerun()


# ----------------------------
# ADMIN PANEL
# ----------------------------
elif st.session_state.role == "Admin":
    st.title("🛡️ Admin Panel")

    render_chat()

    # Reply
    admin_msg = st.text_input("Reply to User:")
    if st.button("Send", key="admin_send") and admin_msg:
        st.session_state.messages.append(("Admin", admin_msg))
        st.experimental_rerun()

    # Show uploaded files
    st.subheader("📂 Uploaded Files")
    for sender, fname in st.session_state.files:
        st.markdown(f"📄 From **{sender}**: {fname}")

    # Logout
    if st.button("Logout"):
        st.session_state.role = None
        st.experimental_rerun()
