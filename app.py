import streamlit as st
import os
import json
import time

CHAT_DIR = "chats"
ADMIN_PASSWORD = "Vishal@9999"  # change this

if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

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


# --- Streamlit App ---
st.title("💬 Chat System")

menu = st.sidebar.radio("Login as:", ["User", "Admin"])

# --- User Section ---
if menu == "User":
    user_id = st.text_input("Enter your User ID (any unique name):")
    if user_id:
        chat_history = load_chat(user_id)

        st.markdown("### Chat Window")
        for chat in chat_history:
            msg_time = chat.get("time", "")
            if chat["role"] == "user":
                st.markdown(f"❓ **You ({msg_time}):** {chat['message']}")
            else:
                st.markdown(f"✅ **Admin ({msg_time}):** {chat['message']}")

        user_msg = st.text_input("Type your message:")
        if st.button("Send"):
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

        # 🔍 Global Search
        st.markdown("## 🔎 Global Search Across All Users")
        global_search = st.text_input("Search for a keyword in all chats:")
        if global_search:
            found = False
            for uid in user_list:
                chat_history = load_chat(uid)
                for chat in chat_history:
                    if global_search.lower() in chat["message"].lower():
                        msg_time = chat.get("time", "")
                        role = "User" if chat["role"] == "user" else "Admin"
                        st.markdown(f"- 👤 **{uid}** [{msg_time}] **{role}:** {chat['message']}")
                        found = True
            if not found:
                st.info("No matches found.")

            st.markdown("---")

        # Show chats per user
        if user_list:
            play_sound = False
            display_users = []
            for uid in user_list:
                history = load_chat(uid)
                if history and history[-1]["role"] == "user":
                    display_users.append(f"🔴 {uid}")
                    play_sound = True
                else:
                    display_users.append(f"🟢 {uid}")

            selected_user = st.selectbox("Select a user:", display_users)
            clean_user = selected_user[2:]  

            chat_history = load_chat(clean_user)

            st.markdown(f"### Chat with {clean_user}")

            for chat in chat_history:
                msg_time = chat.get("time", "")
                if chat["role"] == "user":
                    st.markdown(f"❓ **User ({msg_time}):** {chat['message']}")
                else:
                    st.markdown(f"✅ **You ({msg_time}):** {chat['message']}")

            # Reply
            admin_reply = st.text_input("Your Reply:", key="admin_reply")
            if st.button("Send Reply"):
                if admin_reply:
                    chat_history.append({"role": "admin", "message": admin_reply, "time": timestamp()})
                    save_chat(clean_user, chat_history)
                    st.rerun()

            # Export / Clear / Delete
            st.markdown("---")
            st.warning("⚠️ Danger Zone & Tools")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if chat_history:
                    export_txt = "\n".join([f"[{c['time']}] {c['role'].capitalize()}: {c['message']}" for c in chat_history])
                    st.download_button(
                        "📥 Export TXT",
                        export_txt,
                        file_name=f"{clean_user}_chat.txt",
                        mime="text/plain"
                    )

            with col2:
                if chat_history:
                    export_json = json.dumps(chat_history, indent=2)
                    st.download_button(
                        "📥 Export JSON",
                        export_json,
                        file_name=f"{clean_user}_chat.json",
                        mime="application/json"
                    )

            with col3:
                if st.button("🧹 Clear Chat"):
                    save_chat(clean_user, [])
                    st.success(f"Chat with {clean_user} cleared.")
                    st.rerun()

            with col4:
                if st.button("🗑️ Delete Chat File"):
                    os.remove(get_chat_path(clean_user))
                    st.success(f"Chat file for {clean_user} deleted.")
                    st.rerun()

            # 🔔 Notification sound
            if play_sound:
                st.markdown(
                    """
                    <audio autoplay>
                      <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
                    </audio>
                    """,
                    unsafe_allow_html=True,
                )

        else:
            st.info("No users have started a chat yet.")
