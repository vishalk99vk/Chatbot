import streamlit as st

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of dicts: user, message, file, reply
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "login_success" not in st.session_state:
    st.session_state.login_success = False

# ---------- Login Page ----------
def login():
    st.title("Chat App Login")
    role = st.selectbox("Select Role", ["User", "Admin"])
    st.session_state.role = role

    if role == "User":
        name = st.text_input("Enter your name")
        if st.button("Proceed as User"):
            if name:
                st.session_state.current_user = name
                st.session_state.login_success = True
            else:
                st.error("Please enter your name!")

    elif role == "Admin":
        password = st.text_input("Enter Admin Password", type="password")
        if st.button("Proceed as Admin"):
            if password == "admin123":  # set your admin password here
                st.session_state.current_user = "Admin"
                st.session_state.login_success = True
            else:
                st.error("Incorrect Password!")

# ---------- Chat Interface ----------
def chat_interface():
    st.title(f"Welcome {st.session_state.current_user}")

    if st.session_state.role == "User":
        # File upload
        uploaded_file = st.file_uploader("Upload a file", type=None)
        # Message input
        message = st.text_area("Type your message here")
        if st.button("Send Message"):
            if message:
                st.session_state.messages.append({
                    "user": st.session_state.current_user,
                    "message": message,
                    "file": uploaded_file.name if uploaded_file else None,
                    "reply": None
                })
                st.success("Message sent!")
            else:
                st.error("Please type a message before sending.")

    elif st.session_state.role == "Admin":
        st.subheader("User Messages")
        if not st.session_state.messages:
            st.info("No messages yet.")
        for i, msg in enumerate(st.session_state.messages):
            st.markdown(f"**{msg['user']}**: {msg['message']}")
            if msg["file"]:
                st.markdown(f"Uploaded File: {msg['file']}")
            # Reply box
            reply_key = f"reply_{i}"
            reply = st.text_area(f"Reply to {msg['user']}", value=msg["reply"] or "", key=reply_key)
            send_key = f"send_{i}"
            if st.button(f"Send Reply", key=send_key):
                st.session_state.messages[i]["reply"] = reply
                st.success(f"Replied to {msg['user']}!")

# ---------- Main ----------
if not st.session_state.login_success:
    login()
else:
    chat_interface()
