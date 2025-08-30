import streamlit as st
import os
import json
import time
import re
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import hashlib
import secrets
from pathlib import Path

# -------------------- CONFIG --------------------
CHAT_DIR = Path("chats")
UPLOADS_DIR = Path("uploads")
USERS_FILE = Path("users.json")
ADMIN_PASSWORD = "Vishal@12345"  # <-- change this
BOT_DELAY_MINUTES = 3
BOT_NAME = "🤖 AutoBot"

CHAT_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# -------------------- PASSWORD UTILS (SECURE) --------------------
# Store users as:
# {
#   "alice": {"salt": "<hex>", "hash": "<hex>"},
#   ...
# }
def load_users() -> dict:
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    return {}

def save_users(data: dict) -> None:
    USERS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def hash_password(password: str, salt: bytes) -> bytes:
    # PBKDF2-HMAC-SHA256
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)

def register_user(username: str, password: str) -> bool:
    users = load_users()
    if username in users:
        return False
    salt = secrets.token_bytes(16)
    pw_hash = hash_password(password, salt)
    users[username] = {"salt": salt.hex(), "hash": pw_hash.hex()}
    save_users(users)
    return True

def verify_user(username: str, password: str) -> bool:
    users = load_users()
    info = users.get(username)
    if not info:
        return False
    salt = bytes.fromhex(info["salt"])
    expected = bytes.fromhex(info["hash"])
    return secrets.compare_digest(hash_password(password, salt), expected)

# -------------------- CHAT / FILE HELPERS --------------------
def ts_str() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def chat_path(user_id: str) -> Path:
    return CHAT_DIR / f"{user_id}.json"

def load_chat(user_id: str) -> list:
    p = chat_path(user_id)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return []

def save_chat(user_id: str, history: list) -> None:
    chat_path(user_id).write_text(json.dumps(history, indent=2), encoding="utf-8")

def get_all_user_ids() -> list:
    return sorted([p.stem for p in CHAT_DIR.glob("*.json")])

def user_upload_dir(user_id: str) -> Path:
    d = UPLOADS_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def sanitize_filename(name: str) -> str:
    # Keep it simple: alnum, dot, dash, underscore
    name = os.path.basename(name)
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)

def save_uploaded_file_for_chat(user_id: str, uploaded_file, sender: str) -> Path:
    # sender in {"user","admin"}
    directory = user_upload_dir(user_id)
    safe_name = sanitize_filename(uploaded_file.name)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_name = f"{sender}_{ts}_{safe_name}"
    file_path = directory / final_name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def render_message_bubble(role: str, message: str, when: str):
    if role == "user":
        color, align, who = "#DCF8C6", "right", "🧑‍💻 You"
    elif role == "admin":
        color, align, who = "#E8F0FE", "left", "👨‍💼 Admin"
    else:
        color, align, who = "#FFF4E5", "left", BOT_NAME
    st.markdown(
        f"""
        <div style="text-align:{align}; margin:6px;">
            <div style="background:{color}; padding:10px; border-radius:10px; display:inline-block; max-width:75%;">
                {message}
            </div><br>
            <small>{who} • {when}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -------------------- BOT LOGIC --------------------
def maybe_post_bot_reply(user_id: str, history: list) -> None:
    """Post one bot reply if last user message is older than BOT_DELAY and
    there is no newer admin/bot message after that."""
    if not history:
        return

    # Find last user message
    last_user_idx = None
    for i in range(len(history)-1, -1, -1):
        if history[i]["role"] == "user":
            last_user_idx = i
            break
    if last_user_idx is None:
        return

    # Any admin/bot message after last user message?
    for msg in history[last_user_idx+1:]:
        if msg["role"] in ("admin", "bot"):
            return  # already replied

    # Check age
    try:
        msg_time = datetime.strptime(history[last_user_idx]["time"], "%Y-%m-%d %H:%M:%S")
    except Exception:
        msg_time = datetime.now() - timedelta(minutes=BOT_DELAY_MINUTES+1)

    if datetime.now() - msg_time >= timedelta(minutes=BOT_DELAY_MINUTES):
        history.append({
            "role": "bot",
            "message": "Thanks for your message! A human will reply soon. Meanwhile, can you share more details?",
            "time": ts_str()
        })
        save_chat(user_id, history)

# -------------------- APP --------------------
st.set_page_config(page_title="Live Chat", layout="wide")
st.title("💬 Auto Chat Bot)")

# Auto-refresh (off by default)
if st.sidebar.checkbox("🔄 Auto-refresh every 2s", value=False):
    st_autorefresh(interval=2000, key="refresh_key")

mode = st.sidebar.radio("Use as:", ["User", "Admin"])

# ==================== USER AREA ====================
if mode == "User":
    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

    # --- Register ---
    with tab_register:
        st.subheader("Create an account")
        reg_user = st.text_input("Username (unique)")
        reg_pass = st.text_input("Password", type="password")
        if st.button("Register"):
            if not reg_user or not reg_pass:
                st.error("Please provide both username and password.")
            elif register_user(reg_user, reg_pass):
                st.success("✅ Registered! Go to Login tab.")
            else:
                st.error("Username already exists.")

    # --- Login ---
    with tab_login:
        st.subheader("Login")
        log_user = st.text_input("Username", key="login_user")
        log_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", key="user_login_btn"):
            if verify_user(log_user, log_pass):
                st.session_state.user_auth = True
                st.session_state.user_id = log_user
                st.success(f"Welcome, {log_user}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    # --- Post-login Chat UI ---
    if st.session_state.get("user_auth"):
        user_id = st.session_state["user_id"]
        st.markdown(f"### 💬 Chat — {user_id}")

        # Load and maybe bot reply (if admin hasn't responded)
        history = load_chat(user_id)
        maybe_post_bot_reply(user_id, history)
        history = load_chat(user_id)

        # Render chat
        for item in history:
            msg = item.get("message", "")
            when = item.get("time", ts_str())
            render_message_bubble(item.get("role", "user"), msg, when)
            # If the message includes a file reference, show a download button
            file_path = item.get("file")
            if file_path and Path(file_path).exists():
                with open(file_path, "rb") as fh:
                    st.download_button(
                        label=f"📥 Download {Path(file_path).name}",
                        data=fh,
                        file_name=Path(file_path).name,
                        key=f"usrdl_{file_path}_{when}"
                    )

        # Compose
        with st.form(key="user_compose"):
            col1, col2 = st.columns([3, 2])
            with col1:
                user_text = st.text_input("Message")
            with col2:
                user_file = st.file_uploader("Attach a file (optional)", key="user_upload")
            submitted = st.form_submit_button("Send")
            if submitted:
                entry = {"role": "user", "message": user_text.strip(), "time": ts_str()}
                if user_file is not None:
                    saved = save_uploaded_file_for_chat(user_id, user_file, sender="user")
                    entry["file"] = str(saved)
                    if not entry["message"]:
                        entry["message"] = f"📎 Sent a file: {Path(saved).name}"
                if entry["message"]:
                    history.append(entry)
                    save_chat(user_id, history)
                    st.rerun()
                else:
                    st.warning("Enter a message or attach a file.")

        # Show all files exchanged for this user (both directions)
        st.markdown("### 📂 Files shared in this conversation")
        files_dir = user_upload_dir(user_id)
        files_list = sorted(files_dir.glob("*"))
        if not files_list:
            st.caption("No files yet.")
        else:
            for fp in files_list:
                with open(fp, "rb") as fh:
                    st.download_button(
                        label=f"⬇️ {fp.name}",
                        data=fh,
                        file_name=fp.name,
                        key=f"usr_files_{fp.name}"
                    )

        if st.button("🚪 Logout"):
            st.session_state.user_auth = False
            st.session_state.user_id = None
            st.rerun()

# ==================== ADMIN AREA ====================
elif mode == "Admin":
    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False

    if not st.session_state.admin_auth:
        pw = st.text_input("Admin Password", type="password")
        if st.button("Login as Admin"):
            if pw == ADMIN_PASSWORD:
                st.session_state.admin_auth = True
                st.success("✅ Admin logged in")
                st.rerun()
            else:
                st.error("Wrong admin password.")
    else:
        if st.button("🚪 Logout"):
            st.session_state.admin_auth = False
            st.rerun()

        users = get_all_user_ids()
        if not users:
            st.info("No user chats yet.")
        else:
            selected = st.selectbox("Select user chat:", users)
            st.markdown(f"### 💬 Chat with {selected}")

            history = load_chat(selected)
            maybe_post_bot_reply(selected, history)
            history = load_chat(selected)

            # Show history (with file download)
            for item in history:
                msg = item.get("message", "")
                when = item.get("time", ts_str())
                render_message_bubble(item.get("role", "user"), msg, when)
                file_path = item.get("file")
                if file_path and Path(file_path).exists():
                    with open(file_path, "rb") as fh:
                        st.download_button(
                            label=f"📥 Download {Path(file_path).name}",
                            data=fh,
                            file_name=Path(file_path).name,
                            key=f"admindl_{file_path}_{when}"
                        )

            # Compose (admin -> user)
            with st.form(key="admin_compose"):
                c1, c2 = st.columns([3, 2])
                with c1:
                    admin_text = st.text_input("Your reply")
                with c2:
                    admin_file = st.file_uploader("Attach a file (optional)", key="admin_upload")
                send = st.form_submit_button("Send Reply")
                if send:
                    entry = {"role": "admin", "message": admin_text.strip(), "time": ts_str()}
                    if admin_file is not None:
                        saved = save_uploaded_file_for_chat(selected, admin_file, sender="admin")
                        entry["file"] = str(saved)
                        if not entry["message"]:
                            entry["message"] = f"📎 Sent a file: {Path(saved).name}"
                    if entry["message"]:
                        history.append(entry)
                        save_chat(selected, history)
                        st.rerun()
                    else:
                        st.warning("Enter a message or attach a file.")

            # Files list (both directions)
            st.markdown("### 📂 Files in this conversation")
            files_dir = user_upload_dir(selected)
            files_list = sorted(files_dir.glob("*"))
            if not files_list:
                st.caption("No files yet.")
            else:
                for fp in files_list:
                    with open(fp, "rb") as fh:
                        st.download_button(
                            label=f"⬇️ {fp.name}",
                            data=fh,
                            file_name=fp.name,
                            key=f"admin_files_{fp.name}"
                        )

            # Danger zone: delete chat
            st.divider()
            if st.button("🗑️ Delete Entire Chat", type="secondary"):
                try:
                    chat_path(selected).unlink(missing_ok=True)
                    # Optionally keep files; if you also want to delete files, uncomment:
                    # for f in user_upload_dir(selected).glob("*"):
                    #     f.unlink(missing_ok=True)
                    st.success(f"Deleted chat for '{selected}'.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete chat: {e}")
