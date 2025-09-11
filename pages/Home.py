import streamlit as st
from data_management import save_all_data
import api  # <-- Use your API module
from datetime import datetime
from forms import deploy_forms, handle_form_submission, update_reference_type


def initialize_session_state():
    if "form_mode" not in st.session_state:
        st.session_state.form_mode = None
    if "forms" not in st.session_state:
        st.session_state.forms = {}


def convert_dates_in_record(record):
    if isinstance(record, dict):
        for k, v in record.items():
            if isinstance(v, str):
                try:
                    parsed = datetime.fromisoformat(v)
                    if parsed.time() == datetime.min.time():
                        record[k] = parsed.date()
                    else:
                        record[k] = parsed
                except Exception:
                    pass
            elif isinstance(v, dict):
                convert_dates_in_record(v)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        convert_dates_in_record(item)
    return record


def handle_existing_record(reference_number, reference_type, editable=True):
    if reference_type == "After Sales":
        records = api.get_records(form_type="After Sales")
    else:
        records = api.get_records(form_type="New Reference")

    record = records.get(reference_number)

    if record:
        st.info(f"Record found for Reference Number: {reference_number}")
        if editable:
            record = convert_dates_in_record(record)
            deploy_forms(record)
        return True
    elif reference_number is None or reference_number == "":
        st.info("Please enter a Reference Number.")
        return False
    else:
        st.warning(f"No record found for Reference Number: {reference_number}")
        return False


def show_home():
    st.title("📝 SmartSourcing Forms")
    st.markdown("Welcome! Please choose an action below.")

    col1, col2, col3 = st.columns(3)
    with col1:
        new_form_clicked = st.button("🆕 New Form", use_container_width=True)
    with col2:
        edit_form_clicked = st.button("✏️ Edit Form", use_container_width=True)
    with col3:
        delete_form_clicked = st.button(
            "🗑️ Delete Form", use_container_width=True)

    if "form_mode" not in st.session_state or st.session_state.form_mode is None:
        st.session_state.form_mode = "new"

    if "referenceType" not in st.session_state or st.session_state.referenceType not in ["New Reference", "After Sales"]:
        st.session_state.referenceType = "New Reference"

    reference_type = st.selectbox(
        "**Reference Type**",
        options=["New Reference", "After Sales"],
        index=["New Reference", "After Sales"].index(
            st.session_state.referenceType),
        key="referenceType_select",
        on_change=update_reference_type
    )

    if new_form_clicked:
        st.session_state.form_mode = "new"
    elif edit_form_clicked:
        st.session_state.form_mode = "edit"
    elif delete_form_clicked:
        st.session_state.form_mode = "delete"

    if st.session_state.form_mode == "new":
        deploy_forms(form_data={})

    elif st.session_state.form_mode == "edit":
        reference_number = st.text_input("Enter Reference Number to Edit:").upper()
        st.session_state.record_found = handle_existing_record(
            reference_number, reference_type)

    elif st.session_state.form_mode == "delete":
        reference_number = st.text_input("Enter Reference Number to Delete:").upper()
        if reference_number:
            records = api.get_records(form_type=reference_type)
            if reference_number in records:
                if st.button("❌ Confirm Delete"):
                    api.delete_record(reference_number,reference_type)
                    st.success("Record deleted.")
            else:
                st.warning("Record not found.")


def show_announcements():
    st.header("📢 Announcements")
    st.info("No announcements at the moment.")


def show_logs():
    st.header("📝 Logs")
    st.info("No logs to show.")


def show_profile():
    st.header("👤 Profile")
    st.info("User profile is not yet available.")


def main():
    initialize_session_state()
    show_home()


main()
