import streamlit as st
from datetime import datetime, timedelta
from firebase_config import get_firestore
import requests
from PIL import Image
import io
from datetime import datetime, timezone

# Initialize Firestore DB
db = get_firestore()

# ------------------------ Authentication Check ------------------------


def authenticate():
    return 'current_user' in st.session_state

# ------------------------ Image Handling Utilities ------------------------


def load_image(image_url, default_path='./pics/user.jpg'):
    try:
        if isinstance(image_url, bytes):
            return Image.open(io.BytesIO(image_url))
        if image_url and isinstance(image_url, str):
            if image_url.startswith('http'):
                response = requests.get(image_url, timeout=5)
                if response.status_code == 200:
                    return Image.open(io.BytesIO(response.content))
            elif image_url != default_path:
                return Image.open(image_url)
        return Image.open(default_path)
    except Exception:
        return Image.open(default_path)

# ------------------------ Fetch All Users ------------------------


@st.cache_data(ttl=300, show_spinner="Loading user data...")
def get_all_users():
    try:
        users_ref = db.collection('users')
        status_docs = db.collection('user_status').stream()
        status_data = {doc.id: doc.to_dict() for doc in status_docs}

        users = []
        for doc in users_ref.stream():
            user = doc.to_dict()
            last_sign_in = user.get('last_sign_in')
            users.append({
                'uid': doc.id,
                'email': user.get('email'),
                'display_name': user.get('display_name') or user.get('email', '').split('@')[0],
                'last_sign_in': last_sign_in,
                'photo_url': user.get('profile_pic_url'),
                'last_online': status_data.get(doc.id, {}).get('last_online'),
                'role': user.get('role', 'Member'),
                'department': user.get('department', 'Not specified'),
                'bio': user.get('bio', ''),
                'company': user.get('company', ''),
                'position': user.get('position', ''),
                'address': user.get('address', {}),
                'skills': user.get('skills', []),
                'first_name': user.get('first_name', ''),
                'last_name': user.get('last_name', ''),
                'phone': user.get('phone', '')
            })
        return users
    except Exception as e:
        st.error(f"Error fetching users from Firestore: {e}")
        return []

# ------------------------ Status Utilities ------------------------


def update_last_online(uid):
    try:
        now = datetime.now()
        db.collection('user_status').document(uid).set({
            'last_online': now,
            'updated_at': now
        }, merge=True)
    except Exception as e:
        st.error(f"Error updating last online status: {e}")


def is_user_online(last_online):
    if not last_online:
        return False

    # Convert Firestore timestamp if needed
    if hasattr(last_online, 'to_datetime'):
        last_online = last_online.to_datetime()

    # Convert naive datetime to aware for safe comparison
    if last_online.tzinfo is None:
        last_online = last_online.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    return (now - last_online) < timedelta(minutes=5)



def format_datetime(dt):
    if not dt:
        return "Never"
    now = datetime.now(timezone.utc)
    # Firestore timestamps might be datetime or timestamps in ms
    if isinstance(dt, (int, float)):
        dt = datetime.fromtimestamp(dt / 1000, tz=timezone.utc)
    elif hasattr(dt, 'to_datetime'):  # if Firestore timestamp object
        dt = dt.to_datetime()
    # Ensure dt is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt

    if delta < timedelta(minutes=1):
        return "Just now"
    elif delta < timedelta(hours=1):
        return f"{int(delta.total_seconds() / 60)} minutes ago"
    elif delta < timedelta(days=1):
        return f"{int(delta.total_seconds() / 3600)} hours ago"
    elif delta < timedelta(days=7):
        return f"{delta.days} days ago"
    else:
        return dt.strftime('%b %d, %Y')

# ------------------------ Refresh current_user with latest data ------------------------


def refresh_current_user():
    if 'current_user' in st.session_state and st.session_state['current_user'] is not None:
        uid = st.session_state['current_user']['uid']
        users = get_all_users()
        user = next((u for u in users if u['uid'] == uid), None)
        if user:
            st.session_state['current_user'] = user


# ------------------------ Profile Page ------------------------
@st.cache_data(ttl=60, show_spinner="Loading profile data...")
def get_profile_data(uid):
    """Get cached profile data for a specific user"""
    users = get_all_users()
    return next((u for u in users if u['uid'] == uid), None)

@st.cache_data(ttl=60, show_spinner="Loading team data...")
def get_team_data(current_uid, search_query, status_filter, sort_option):
    """Get cached team data with filtering and sorting"""
    users = get_all_users()
    users_filtered = [u for u in users if u['uid'] != current_uid]
    
    if search_query:
        users_filtered = [
            u for u in users_filtered
            if search_query.lower() in u['display_name'].lower()
            or search_query.lower() in u['email'].lower()
        ]
    
    if status_filter != "All":
        users_filtered = [
            u for u in users_filtered
            if is_user_online(u['last_online']) == (status_filter == "Online")
        ]
    

    if sort_option == "Last Active":
        users_sorted = sorted(
            users_filtered,
            key=lambda u: (u['last_online'] or datetime.min.replace(tzinfo=timezone.utc)).astimezone(timezone.utc),
            reverse=True
        )

    elif sort_option == "Name":
        users_sorted = sorted(
            users_filtered, key=lambda u: u['display_name'].lower())
    else:
        users_sorted = sorted(
            users_filtered, key=lambda u: u['last_sign_in'] or 0, reverse=True)
    
    return users_sorted

def profile_page():
    if not authenticate():
        st.warning("Please log in to view your profile.")
        return

    # Refresh current_user data with latest Firestore info
    refresh_current_user()

    user = st.session_state['current_user']
    if not user:
        st.error("User data not found")
        return
    update_last_online(user['uid'])

    # Get cached profile data
    user = get_profile_data(user['uid'])
    if not user:
        st.error("User data not found")
        return

    # Header
    st.markdown("""
        <style>
            .profile-header {
                background-color: #f6f8fa;
                border-radius: 12px;
                padding: 2rem 1rem;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
            .profile-header h1 {
                text-align: center;
                color: #4B8BBE;
                font-family: Helvetica;
            }
        </style>
    """, unsafe_allow_html=True)

    # Load profile image, use default if not available
    img = load_image(user.get('photo_url') or "./pics/user.jpg")
    # Display profile image and name side by side, image circular and small
    col_img, col_name = st.columns([1, 25])
    with col_img:
        st.image(img, width=80, caption="", output_format="PNG", clamp=True)
        st.markdown(
            """
            <style>
            .element-container img {
                border-radius: 50% !important;
                object-fit: cover;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    with col_name:
        st.markdown(f"""
            <h2 style='
                color: #4B8BBE;
                border-bottom: 2px solid #e9ecef;
                margin-top: 0;
            '>
            {user.get('display_name')}
            </h2>
            """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
            st.markdown(
                f"<div style='margin-bottom: 12px;'><b>👤 First Name:</b><br>{user.get('first_name', '')}</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='margin-bottom: 12px;'><b>📧 Email:</b><br>{user.get('email')}</div>", unsafe_allow_html=True)
            if user.get('last_sign_in'):
                st.markdown(
                    f"<div style='margin-bottom: 12px;'><b>⏱ Last Login:</b><br>{format_datetime(user['last_sign_in'])}</div>", unsafe_allow_html=True)
            if user.get('company'):
                st.markdown(
                    f"<div style='margin-bottom: 12px;'><b>🏢 Company:</b><br>{user['company']}</div>", unsafe_allow_html=True)
            if user.get('phone'):
                st.markdown(
                    f"<div style='margin-bottom: 12px;'><b>📱 Phone:</b><br>{user['phone']}</div>", unsafe_allow_html=True)

    with col_b:
            st.markdown(
                f"<div style='margin-bottom: 12px;'><b>👥 Last Name:</b><br>{user.get('last_name', '')}</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='margin-bottom: 12px;'><b>🆔 User ID:</b><br><code>{user.get('uid')}</code></div>", unsafe_allow_html=True)
            if user.get('position'):
                st.markdown(
                    f"<div style='margin-bottom: 12px;'><b>💼 Position:</b><br>{user['position']}</div>", unsafe_allow_html=True)
            if user.get('skills'):
                st.markdown(
                    f"<div style='margin-bottom: 12px;'><b>🛠️ Skills:</b><br>{', '.join(user['skills'])}</div>", unsafe_allow_html=True)

    if user.get('bio'):
            st.markdown(
                f"<div style='margin: 12px 0 12px;'><b>📝 Bio:</b><br>{user['bio']}</div>", unsafe_allow_html=True)

    if user.get('address'):
            address = user['address']
            address_str = ", ".join(
                filter(None, [
                    address.get('street', ''),
                    address.get('city', ''),
                    address.get('state', ''),
                    address.get('zip_code', ''),
                    address.get('country', '')
                ])
            )
            st.markdown(
                f"<div style='margin-bottom: 12px;'><b>🏠 Address:</b><br>{address_str}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ------------------------ Team Members ------------------------
    st.markdown("<h2 style='color:#4B8BBE;'>👥 Team Members</h2>",
                unsafe_allow_html=True)

    search_col, filter_col = st.columns([3, 1])
    with search_col:
        search_query = st.text_input("Search by name or email", "")
    with filter_col:
        status_filter = st.selectbox("Status", ["All", "Online", "Offline"])

    sort_option = st.selectbox(
        "Sort by", ["Last Active", "Name", "Last Login"])
    
    # Get cached team data with current filters
    team_members = get_team_data(
        user['uid'], 
        search_query, 
        status_filter, 
        sort_option
    )

    cols = st.columns(3)
    for idx, u in enumerate(team_members):
        online = is_user_online(u['last_online'])
        status_color = "#4CAF50" if online else "#F44336"
        address = u.get('address', {})
        skills = ', '.join(u.get('skills', [])) or 'N/A'
        bio = u.get('bio', '')
        company = u.get('company', 'N/A')
        position = u.get('position', 'N/A')

        with cols[idx % 3]:
            # Load and display user profile image using PIL for local or remote images
            team_img = load_image(u.get('photo_url') or "./pics/user.jpg")
            st.markdown(f"""
                <div style="
                    background-color: #f6f8fa;
                    border-radius: 10px;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
                    border-left: 4px solid {status_color};
                    display: flex;
                    align-items: flex-start;
                    gap: 1rem;
                ">
                    <div>
                        <img src="data:image/png;base64,{Image_to_base64(team_img)}" style="width:50px;height:50px;border-radius:50%;object-fit:cover;" />
                    </div>
                    <div style="flex:1;">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">{u['display_name']}</div>
                        <div style="font-size: 0.85rem; margin-bottom: 0.5rem;">
                            <div>📧 {u['email']}</div>
                            <div>🏢 {company}</div>
                            <div>📍 {address.get('city', '')}, {address.get('country', '')}</div>
                            <div>🛠️ Skills: {skills}</div>
                            <div>📝 {bio}</div>
                        </div>
                        <div style="font-size: 0.8rem; color: #888;">
                            <div>🕒 Last Active: {format_datetime(u['last_online'])}</div>
                            <div>🔑 Last Login: {format_datetime(u['last_sign_in'])}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
          

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

import base64

def Image_to_base64(img):
    """Convert a PIL Image to a base64-encoded string."""
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

profile_page()