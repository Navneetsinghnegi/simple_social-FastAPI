import streamlit as st
import requests
import base64
import urllib.parse
import os

# ================= CONFIG =================
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Simple Social", layout="wide")

# ================ SESSION STATE ============
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
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
                login_data = {"username": email, "password": password}
                response = requests.post(f"{API_URL}/auth/jwt/login", data=login_data)

                if response.status_code == 200:
                    token_data = response.json()
                    st.session_state.token = token_data["access_token"]

                    user_response = requests.get(f"{API_URL}/users/me", headers=get_headers())
                    if user_response.status_code == 200:
                        st.session_state.user = user_response.json()
                        st.rerun()
                    else:
                        st.error("Failed to get user info")
                else:
                    st.error("Invalid email or password!")

        with col2:
            if st.button("Sign Up", type="secondary", use_container_width=True):
                signup_data = {"email": email, "password": password}
                response = requests.post(f"{API_URL}/auth/register", json=signup_data)

                if response.status_code == 201:
                    st.success("Account created! Click Login now.")
                else:
                    st.error(response.json().get("detail", "Registration failed"))
    else:
        st.info("Enter your email and password above")


# ================= UPLOAD ==================
def upload_page():
    st.title("📸 Share Something")

    uploaded_file = st.file_uploader(
        "Choose media",
        type=['png', 'jpg', 'jpeg', 'mp4', 'avi', 'mov', 'mkv', 'webm']
    )
    caption = st.text_area("Caption:", placeholder="What's on your mind?")

    if uploaded_file and st.button("Share", type="primary"):
        with st.spinner("Uploading..."):
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                )
            }
            data = {"caption": caption}

            response = requests.post(
                f"{API_URL}/upload",
                files=files,
                data=data,
                headers=get_headers()
            )

            if response.status_code == 200:
                st.success("Posted!")
                st.rerun()
            else:
                st.error(response.json().get("detail", "Upload failed"))


# ================= IMAGEKIT UTILS ==========
def encode_text_for_overlay(text):
    if not text:
        return ""
    base64_text = base64.b64encode(text.encode()).decode()
    return urllib.parse.quote(base64_text)


def create_transformed_url(original_url, caption=None):
    if not caption:
        return original_url

    encoded_caption = encode_text_for_overlay(caption)
    text_overlay = f"l-text,ie-{encoded_caption},ly-N20,lx-20,fs-100,co-white,bg-000000A0,l-end"

    parts = original_url.split("/")
    base_url = "/".join(parts[:4])
    file_path = "/".join(parts[4:])
    return f"{base_url}/tr:{text_overlay}/{file_path}"


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

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{post['email']}** • {post['created_at'][:10]}")
        with col2:
            if post["is_owner"]:
                if st.button("🗑️", key=f"delete_{post['id']}"):
                    r = requests.delete(
                        f"{API_URL}/posts/{post['id']}",
                        headers=get_headers()
                    )
                    if r.status_code == 200:
                        st.success("Deleted")
                        st.rerun()
                    else:
                        st.error("Delete failed")

        if post["file_type"] == "image":
            st.image(create_transformed_url(post["url"], post["caption"]), width=300)
        else:
            st.video(post["url"], width=300)
            st.caption(post["caption"])


# ================= MAIN ====================
if st.session_state.user is None:
    login_page()
else:
    st.sidebar.title(f"👋 Hi {st.session_state.user['email']}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.token = None
        st.rerun()

    page = st.sidebar.radio("Navigate:", ["🏠 Feed", "📸 Upload"])
    feed_page() if page == "🏠 Feed" else upload_page()
