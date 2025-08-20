# firebase_config.py
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage, db as realtime_db
import streamlit as st

# Initialize Firebase services
def initialize_firebase():
    key_dict = json.loads(st.secrets["KEY"])
    project_name = st.secrets["PROJECT_NAME"]
    database_url = st.secrets["LINK"]
    storage_bucket = st.secrets["BUCKET"]  # Should be "procurement-3745e.appspot.com"
    
    # Initialize Firebase app if not already initialized
    if not firebase_admin._apps:
        cred = credentials.Certificate(key_dict)
        firebase_app = firebase_admin.initialize_app(
            cred,
            {
                'databaseURL': database_url,
                'storageBucket': storage_bucket
            }
        )
    
    # Initialize individual services
    firestore_db = firestore.client()
    auth_client = auth
    realtime_db_client = realtime_db
    storage_client = storage.bucket(storage_bucket)  # Explicitly specify the bucket name
    
    return firestore_db, auth_client, realtime_db_client, storage_client

try:
    firestore_db, auth_client, realtime_db_client, storage_client = initialize_firebase()
except ValueError as e:
    st.error(f"Firebase initialization error: {e}")
    raise

def get_firestore():
    """Return Firestore database instance"""
    return firestore_db

def get_auth():
    """Return Firebase Auth instance"""
    return auth_client

def get_realtime_db():
    """Return Realtime Database instance"""
    return realtime_db_client

def get_storage():
    """Return Cloud Storage bucket instance"""
    return storage_client