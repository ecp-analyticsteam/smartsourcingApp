# api.py
import datetime
import json
import firebase_admin
from firebase_admin import credentials, firestore, db as realtime_db
from google.oauth2 import service_account
import streamlit as st
from functools import lru_cache
from datetime import datetime

# Initialize Firebase with proper error handling


def initialize_firebase():
    if not firebase_admin._apps:
        try:
            # Get configuration from Streamlit secrets
            key_dict = json.loads(st.secrets["KEY"])
            database_url = st.secrets.get("LINK")

            if not database_url:
                raise ValueError("Database URL is missing in secrets")

            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred, {
                'databaseURL': database_url
            })
            return True
        except json.JSONDecodeError:
            st.error("Invalid service account JSON in secrets")
            raise
        except ValueError as e:
            st.error(f"Firebase configuration error: {e}")
            raise
        except Exception as e:
            st.error(f"Failed to initialize Firebase: {e}")
            raise
    return True


# Initialize Firebase
if initialize_firebase():
    db = firestore.client()
    realtime_db = firebase_admin.db
    auth = firebase_admin.auth
else:
    st.error("Firebase initialization failed. Check your configuration.")
    st.stop()


@st.cache_data(ttl=300)
def get_records(form_type="New Reference"):
    try:
        if form_type == "New Reference":
            ref = realtime_db.reference('/forms')
        elif form_type == "After Sales":
            ref = realtime_db.reference('/aftersales')
        else:
            raise ValueError(
                "Invalid form type. Must be 'New Reference' or 'After Sales'.")
        records = ref.get() or {}
        return {k: convert_dates_in_record(v) for k, v in records.items()}
    except Exception as e:
        st.error(f"Error getting records: {e}")
        return {}


def save_record(reference_number, data, form_type,type):
    try:
        get_records.clear()
        if not reference_number or any(c in reference_number for c in '$#[]/.'):
            raise ValueError("Invalid reference number for Firebase path.")

        # Determine the node based on form_type
        if form_type == "New Reference":
            node_path = f'/forms/{reference_number}'
        elif form_type == "After Sales":
            node_path = f'/aftersales/{reference_number}'
        else:
            raise ValueError(
                "Invalid form type. Must be 'New Reference' or 'After Sales'.")

        node_ref = realtime_db.reference(node_path)
        if type.lower() == "create" and node_ref.get() is not None:
            return st.error("A record with this reference number already exists.")
        else:
            node_ref.set(data)
        log_user_action(f"{type.upper()} Records", data, reference_number)
        st.success("All forms submitted successfully!")
        st.balloons()

        return True
    except Exception as e:
        st.error(f"Error saving record: Save the current form befor saving all form.")
        return False


def get_latest_reference_number():
    try:
        records = get_records()
        if not records:
            return None
        latest_ref = max(records.keys())
        return latest_ref
    except Exception as e:
        st.error(f"Error getting latest reference number: {e}")
        return None


def get_latest_aftersales_reference_number():
    try:
        ref = realtime_db.reference('/aftersales')
        records = ref.get() or {}
        if not records:
            return None
        latest_ref = max(records.keys())
        return latest_ref
    except Exception as e:
        st.error(f"Error getting latest aftersales reference number: {e}")
        return None


def delete_record(reference_number, reference_type="New Reference"):
    try:
        get_records.clear()
        if not reference_number:
            raise ValueError(
                "Reference number is required to delete a record.")
        if reference_type == "New Reference":
            node_path = f'/forms/{reference_number}'
        elif reference_type == "After Sales":
            node_path = f'/aftersales/{reference_number}'
        else:
            raise ValueError(
                "Invalid reference type. Must be 'New Reference' or 'After Sales'.")
        node_ref = realtime_db.reference(node_path)
        record_data = node_ref.get()
        print(record_data)
        node_ref.delete()
        log_user_action("Delete Record", record_data, reference_number)
        return True
    except Exception as e:
        st.error(f"Error deleting record: {e}")
        return False


@st.cache_data(ttl=60)
def get_logs():
    try:
        ref = realtime_db.reference('/logs')
        return ref.get() or {}
    except Exception as e:
        st.error(f"Error getting logs: {e}")
        return {}


def save_log(log_id, data):
    try:
        get_logs.clear()
        if not log_id or any(c in log_id for c in '$#[]/.'):
            raise ValueError("Invalid log ID for Firebase path.")

        node_ref = realtime_db.reference(f'/logs/{log_id}')
        node_ref.set(data)
        return True
    except Exception as e:
        st.error(f"Error saving log: {e}")
        return False


def delete_log(log_id):
    try:
        get_logs.clear()
        if not log_id:
            raise ValueError("Log ID is required to delete a log entry.")

        node_ref = realtime_db.reference(f'/logs/{log_id}')
        node_ref.delete()
        return True
    except Exception as e:
        st.error(f"Error deleting log: {e}")
        return False


@st.cache_data(ttl=60)
def get_announcements():
    try:
        ref = realtime_db.reference('/announcements')
        return ref.get() or {}
    except Exception as e:
        st.error(f"Error getting announcements: {e}")
        return {}


def save_announcement(announcement_id, data):
    try:
        get_announcements.clear()
        if not announcement_id or any(c in announcement_id for c in '$#[]/.'):
            raise ValueError("Invalid announcement ID for Firebase path.")

        node_ref = realtime_db.reference(f'/announcements/{announcement_id}')
        node_ref.set(data)
        return True
    except Exception as e:
        st.error(f"Error saving announcement: {e}")
        return False


def delete_announcement(announcement_id):
    try:
        get_announcements.clear()
        if not announcement_id:
            raise ValueError(
                "Announcement ID is required to delete an announcement.")

        node_ref = realtime_db.reference(f'/announcements/{announcement_id}')
        node_ref.delete()
        return True
    except Exception as e:
        st.error(f"Error deleting announcement: {e}")
        return False


def convert_dates_in_record(record):
    if isinstance(record, dict):
        for k, v in record.items():
            if isinstance(v, str):
                try:
                    parsed = datetime.fromisoformat(v)
                    record[k] = parsed.date() if parsed.time(
                    ) == datetime.min.time() else parsed
                except Exception:
                    pass
            elif isinstance(v, dict):
                convert_dates_in_record(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        convert_dates_in_record(item)
    return record


def log_user_action(action, changed_details, reference_number):
    try:
        firestore_db = db
        user_ref = firestore_db.collection('users').document(
            st.session_state.current_user['uid'])
        user_data = user_ref.get().to_dict()
        user_name = user_data.get('first_name', 'Unknown')
        company_value = user_data.get('company', '')
        user_email = user_data.get('email', '')
        user_last_name = user_data.get('last_name', '')
        user_display_name = f"{user_name} {user_last_name}".strip()

        print(user_data)
        log_entry = {
            "action": action,
            "changedDetails": changed_details,
            "referenceNumber": reference_number,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user": {
                "department": company_value,
                "displayName": user_name,
                "email": user_email,
                "name": user_display_name
            }
        }

        log_ref = firestore_db.collection('logs').add(log_entry)
        # Also save to Realtime Database under /logs/{timestamp}
        timestamp_key = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        realtime_db.reference(f'/logs/{timestamp_key}').set(log_entry)
        return True
    except Exception as e:
        st.error(f"Error logging user action: {e}")
        return False
