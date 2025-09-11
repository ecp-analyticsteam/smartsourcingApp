import json
import toml
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from google.oauth2 import service_account
from firebase_admin import db as realtime_db


# output_file = '.streamlit/secrets.toml'

# with open("firestore-key.json") as json_file:
#     json_text = json_file.read()

# config = {"textkey":json_text}
# toml_config = toml.dumps(config)

# with open(output_file,"w") as target:
#     target.write(toml_config)
