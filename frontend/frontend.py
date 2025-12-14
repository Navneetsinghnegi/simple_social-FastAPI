import streamlit as st
import requests
import os
from datetime import datetime

# ================= CONFIG =================
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Simple Social", layout="wide")

# ================ SESSION STATE ============
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None


def get_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


# ================= AUTH ====================
def login_page():
    st.title("🚀 Welcome to Simple Social")

    email = st.text_input("Email:")
    password = st.text_input("Password:", type="password")

    if email and password:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Login", type="primary", use_container_width=True):
                response = requests.post(
                    f"{API_URL}/auth/jwt/login",
                    data={"username": email, "password": password},
                )

                if response.status_code == 200:
                    st.session_state.token = response.json()["access_token"]
                    user_resp = requests.get(
                        f"{API_URL}/users/me", headers=get_headers()
                    )
                    if user_resp.status_code == 200:
                        st.session_state.user = user_resp.json()
                        st.rerun()
                else:
                    st.error("Invalid email or password")

        with col2:
            if st.button("Sign Up", use_container_width=True):
                response = requests.post(
                    f"{API_URL}/auth/register",
                    json={"email": email, "password": password},
                )
                if response.status_code == 201:
                    st.success("Account created. Login now.")
                else:
                    st.error(response.json().get("detail", "Registration failed"))
    else:
        st.info("Enter email and password")


# ================= UPLOAD ==================
def upload_page():
    st.title("📸 Share Something")

    uploaded_file = st.file_uploader(
        "Choose media",
        type=["png", "jpg", "jpeg", "mp4", "avi", "mov", "mkv", "webm"],
    )
    caption = st.text_area("Caption", placeholder="What's on your mind?")

    if uploaded_file and st.button("Share", type="primary"):
        with st.spinner("Uploading..."):
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type,
                )
            }
            response = requests.post(
                f"{API_URL}/upload",
                files=files,
                data={"caption": caption},
                headers=get_headers(),
            )

            if response.status_code == 200:
                st.success("Posted!")
                st.rerun()
            else:
                st.error(response.json().get("detail", "Upload failed"))


# ================= FEED ====================
def feed_page():
    st.title("🏠 Feed")

    response = requests.get(f"{API_URL}/feed", headers=get_headers())
    if response.status_code != 200:
        st.error("Failed to load feed")
        return

    posts = response.json()["posts"]
    if not posts:
        st.info("No posts yet!")
        return

    for post in posts:
        st.markdown("---")

        # ✅ Format date nicely
        created_at = datetime.fromisoformat(post["created_at"])
        formatted_date = created_at.strftime("%d %b %Y")

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{post['email']}** • {formatted_date}")
        with col2:
            if post["is_owner"]:
                if st.button("🗑️", key=f"delete_{post['id']}"):
                    r = requests.delete(
                        f"{API_URL}/posts/{post['id']}",
                        headers=get_headers(),
                    )
                    if r.status_code == 200:
                        st.success("Deleted")
                        st.rerun()

        # ✅ Media display (NO caption overlay)
        if post["file_type"] == "image":
            st.image(post["url"], width=300)
        else:
            st.video(post["url"], width=300)

        # ✅ Caption below media ONLY if present
        caption = post.get("caption")
        if caption and caption.strip():
            st.caption(caption)


# ================= MAIN ====================
if st.session_state.user is None:
    login_page()
else:
    st.sidebar.title(f"👋 Hi {st.session_state.user['email']}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.token = None
        st.rerun()

    page = st.sidebar.radio("Navigate", ["🏠 Feed", "📸 Upload"])
    feed_page() if page == "🏠 Feed" else upload_page()

