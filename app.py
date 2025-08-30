import streamlit as st

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []  # store all messages as dict
if "files" not in st.session_state:
    st.session_state.files = []  # store files uploaded
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "role" not in st.session_state:
    st.session_state.role = None

# Function to handle login
def login():
    role = st.selectbox("Select Role", ["User", "Admin"])
    st.session_state.role = role

    if role == "User":
        name = st.text_input("Enter your name")
        if st.button("Proceed") and name:
            st.session_state.current_user = name
            st.session_state.login_success = True
    elif role == "Admin":
        password = st.text_input("Enter Admin Password", type="password")
        if st.button("Proceed") and password == "admin123":  # example password
            st.session_state.current_user = "Admin"
            st.session_state.login_success = True
        elif st.button("Proceed") and password != "admin123":
            st.error("Incorrect Password!")

# Function to display messages for user/admin
def chat_interface():
    st.header(f"Welcome {st.session_state.current_user}")

    if st.session_state.role == "User":
        # File upload
        uploaded_file = st.file_uploader("Upload a file", type=None)
        # Message input
        message = st.text_area("Type your message here")
        if st.button("Send"):
            st.session_state.messages.append({
                "user": st.session_state.current_user,
                "message": message,
                "file": uploaded_file.name if uploaded_file else None,
                "reply": None
            })
            st.success("Message sent!")

    elif st.session_state.role == "Admin":
        st.subheader("User Messages")
        for i, msg in enumerate(st.session_state.messages):
            st.markdown(f"**{msg['user']}**: {msg['message']}")
            if msg["file"]:
                st.markdown(f"Uploaded File: {msg['file']}")
            # Reply box
            reply = st.text_area(f"Reply to {msg['user']}", key=f"reply_{i}")
            if st.button(f"Send Reply to {msg['user']}", key=f"send_{i}"):
                st.session_state.messages[i]["reply"] = reply
                st.success(f"Replied to {msg['user']}!")

# Main logic
if "login_success" not in st.session_state:
    st.session_state.login_success = False

if not st.session_state.login_success:
    login()
else:
    chat_interface()
