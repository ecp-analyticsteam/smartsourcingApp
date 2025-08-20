import datetime
import uuid
import streamlit as st
# Then other imports
from firebase_config import get_firestore, get_auth, get_realtime_db, get_storage
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError
# from firebase_admin import firestore  # Removed unused import
from PIL import Image
import io
import uuid
import datetime

# MUST BE FIRST - Streamlit page configuration
st.set_page_config(
    page_title="Smart Sourcing",
    page_icon="🔐",
    layout="wide"
)

# Initialize Firebase services
# Get services
db = get_firestore()
auth = get_auth()
rtdb = get_realtime_db()
storage_client = get_storage()
firestore_db = get_firestore()
# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None


def login(username, _):
    try:
        user = auth.get_user_by_email(username)
        if user.email_verified:
            st.session_state.logged_in = True
            st.session_state.current_user = {
                'email': user.email,
                'uid': user.uid
            }
            st.rerun()
        else:
            st.error("Email not verified. Please check your email.")
            link = auth.generate_email_verification_link(username)
            send_verification_email(username, link)

    except auth.UserNotFoundError:
        st.error("User not found. Please check your email or sign up.")
    except FirebaseError as e:
        st.error(f"Authentication error: {e}")
    except Exception as e:
        st.error(f"Error during login: {e}")


def signup(email, password, user_data):
    try:
        user = auth.create_user(
            email=email,
            password=password,
            email_verified=False
        )

        # Upload profile picture if provided
        profile_pic_url = ""
        if user_data.get('profile_pic'):
            profile_pic_url = upload_profile_picture(
                user.uid, user_data['profile_pic'])

        # Create user document in Firestore
        user_doc = {
            'email': email,
            'created_at': datetime.datetime.now(),
            'role': 'user',
            'first_name': user_data.get('first_name', ''),
            'last_name': user_data.get('last_name', ''),
            'company': user_data.get('company', ''),
            'position': user_data.get('position', ''),
            'phone': user_data.get('phone', ''),
            'address': {
                'street': user_data.get('street', ''),
                'city': user_data.get('city', ''),
                'state': user_data.get('state', ''),
                'zip_code': user_data.get('zip_code', ''),
                'country': user_data.get('country', '')
            },
            'profile_pic_url': profile_pic_url,
            'skills': user_data.get('skills', []),
            'bio': user_data.get('bio', '')
        }
        # Show a loader while processing
        with st.spinner("Creating your account..."):
            # Save to Firestore
            firestore_db.collection('users').document(user.uid).set(user_doc)

            # Send verification email
            link = auth.generate_email_verification_link(email)
            send_verification_email(email, link)

        st.success(
            "Account created successfully! Please check your email to verify your account.")

    except auth.EmailAlreadyExistsError:
        st.error("This email is already registered. Please log in instead.")
    except FirebaseError as e:
        st.error(f"Error creating user: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")


def upload_profile_picture(user_id, image_file):
    try:
        # Generate unique filename
        filename = f"profile_pics/{user_id}/{uuid.uuid4()}.jpg"

        # Create blob in Firebase Storage
        blob = storage_client.blob(filename)

        # Process image
        img = Image.open(image_file)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        # Upload to Firebase Storage
        blob.upload_from_string(img_byte_arr, content_type='image/jpeg')

        # Get download URL
        blob.make_public()
        return blob.public_url

    except Exception as e:
        st.error(f"Error uploading profile picture: {e}")
        return ""


def send_verification_email(email, verification_link):
    try:
        sender_email = st.secrets["EMAIL"]
        sender_password = st.secrets["PASSWORD"]
        sender_name = "Smart Sourcing"

        # Construct MIME email
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = email
        msg["Subject"] = "Verify Your Smart Sourcing Account"

        # Email content
        text_body = f"""Welcome to Smart Sourcing!\n\nPlease verify your email by clicking this link:\n{verification_link}\n\nIf you did not create an account, you can ignore this email."""

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Welcome to Smart Sourcing!</h2>
                <p>Please click the button below to verify your email address:</p>
                <a href="{verification_link}" style="
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                    font-weight: bold;
                ">Verify Email</a>
                <p>If you didn't create an account, you can safely ignore this message.</p>
            </body>
        </html>
        """

        # Attach both plain text and HTML
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        # Send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())

    except Exception as e:
        st.error("Failed to send verification email.")
        st.exception(e)


def logout():
    st.session_state.clear()
    st.rerun()


if st.session_state.logged_in:
    if st.sidebar.button("Logout"):
        logout()

    if st.session_state.logged_in:
        # Display user profile if available
        user_ref = firestore_db.collection('users').document(st.session_state.current_user['uid'])
        user_data = user_ref.get().to_dict()

        pages = {
            "📝 Tasks": [
                st.Page("pages/Home.py", title="🏠 Home"),
                st.Page("pages/View Tables.py", title="📊 View Tables"),
            ],
            "🛠️ Utilities": [
                st.Page("pages/Logs.py", title="📜 Logs"),
                st.Page("pages/Users.py", title="👥 Users"),
                st.Page("pages/Announcements.py", title="📢 Announcement"),
            ],
        }

if st.session_state.logged_in:
    pg = st.navigation(pages)
    pg.run()


else:
    st.title("Smart Sourcing Platform")

    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                login(email, password)

    with signup_tab:
        with st.form("signup_form", clear_on_submit=True):
            st.subheader("Basic Account Setup")

            # Essential fields only
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name*")
            with col2:
                last_name = st.text_input("Last Name*")

            email = st.text_input("Email*")

            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("Password*", type="password")
            with col2:
                confirm_password = st.text_input(
                    "Confirm Password*", type="password")

            # Profile picture upload
            profile_pic = st.file_uploader("Profile Picture (Optional)",
                                           type=["jpg", "jpeg", "png"],
                                           accept_multiple_files=False,
                                           help="Square images work best")

            # Optional minimal profile
            company = st.text_input("Company (Optional)")
            position = st.text_input("Position (Optional)")
            phone = st.text_input("Phone (Optional)")
            bio = st.text_area("Bio (Optional)", max_chars=200)

            st.subheader("Address (Optional)")
            street = st.text_input("Street")
            city = st.text_input("City")
            state = st.text_input("State")
            zip_code = st.text_input("Zip Code")
            country = st.text_input("Country")

            st.subheader("Skills (Optional)")
            skills = st.text_input("Skills (comma separated)")

            submitted = st.form_submit_button("Create Account")

            if submitted:
                if not all([first_name, last_name, email, password, confirm_password]):
                    st.error("Please complete all required fields")
                elif password != confirm_password:
                    st.error("Passwords don't match")
                else:
                    user_data = {
                        'first_name': first_name.strip(),
                        'last_name': last_name.strip(),
                        'company': company.strip(),
                        'position': position.strip(),
                        'phone': phone.strip(),
                        'profile_pic': profile_pic,
                        'bio': bio.strip(),
                        'street': street.strip(),
                        'city': city.strip(),
                        'state': state.strip(),
                        'zip_code': zip_code.strip(),
                        'country': country.strip(),
                        'skills': [s.strip() for s in skills.split(",") if s.strip()] if skills else []
                    }
                    signup(email, password, user_data)
