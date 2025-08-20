import streamlit as st
from datetime import datetime

def initialize_session_state():
    """Initialize session state variables"""
    if "forms" not in st.session_state:
        st.session_state.forms = {}
    if "edit_rn" not in st.session_state:
        st.session_state.edit_rn = None

def reset_form_fields():
    """Clear all form fields and reset edit state"""
    st.session_state.edit_rn = None
    for key in [
        "referenceNumber", "name", "pic", "status", "cpoDate", "customerPoNo", 
        "rfqDate", "vendorQuoteDate", "date", "quotationNumber", "quotationDate", 
        "prfbackOrder", "details", "bofApproval", "bofNo", "forInvoice", 
        "bofDate", "invoiceDateBilling", "receivedDateBilling", "invoiceNumberBilling", 
        "receivedByBilling", "receivedByRequest", 
        "refNo", "receivedDateRequest", "refDate", "rfpApproval", "rfpDate", 
        "rfpNo", "epoNo", "invoiceAmount", "invoiceDate", "invoiceNo", 
        "poDate", "sentByandDate", "supplierName"
    ]:
        if key in st.session_state:
            del st.session_state[key]

def load_form_data(rn):
    """Load form data into session state for editing"""
    if rn in st.session_state.forms:
        form_data = st.session_state.forms[rn]
        for key, value in form_data.items():
            st.session_state[key] = value
        st.session_state.edit_rn = rn


def handle_form_management():
    """Handle form management UI and operations"""
    st.markdown("### Manage Forms")
    cols = st.columns([1, 1, 1, 1])
    
    with cols[0]:
        if st.button("➕ Add New Form"):
            reset_form_fields()

    with cols[1]:
        existing_rns = list(st.session_state.forms.keys())
        edit_rn = st.selectbox(
            "Select Form to Edit (by RN)", 
            [""] + existing_rns,
            key="edit_selectbox"
        )
        if st.button("✏️ Edit Selected Form") and edit_rn:
            load_form_data(edit_rn)

    with cols[2]:
        delete_rn = st.selectbox(
            "Select Form to Delete (by RN)", 
            [""] + existing_rns,
            key="delete_selectbox"
        )
        if st.button("🗑️ Delete Selected Form") and delete_rn:
            del st.session_state.forms[delete_rn]
            st.success(f"Form with RN {delete_rn} deleted.")
            reset_form_fields()
            st.rerun()

    with cols[3]:
        if st.button("🔄 Refresh Form List"):
            st.rerun()

    st.write(f"**Total Forms Saved:** {len(st.session_state.forms)}")

def save_all_data():
    """Collect and return all form data for submission"""
    all_data = {
        "customerForm": {
            "referenceNumber": st.session_state.get("referenceNumber", ""),
            "name": st.session_state.get("name", ""),
            "pic": st.session_state.get("pic", ""),
            "status": st.session_state.get("status", ""),
            "cpoDate": str(st.session_state.get("cpoDate", "")),
            "customerPoNo": st.session_state.get("customerPoNo", ""),
            "rfqDate": str(st.session_state.get("rfqDate", "")),
            "vendorQuoteDate": str(st.session_state.get("vendorQuoteDate", "")),
            "date": str(st.session_state.get("date", "")),
            "quotationNumber": st.session_state.get("quotationNumber", ""),
            "quotationDate": str(st.session_state.get("quotationDate", "")),
            "prfbackOrder": st.session_state.get("prfbackOrder", ""),
            "details": st.session_state.get("details", ""),
        },
        "billingOrderForm": {
            "bofApproval": st.session_state.get("bofApproval", ""),
            "bofNo": st.session_state.get("bofNo", ""),
            "forInvoice": st.session_state.get("forInvoice", ""),
            "bofDate": str(st.session_state.get("bofDate", "")),
            "invoiceDateBilling": str(st.session_state.get("invoiceDateBilling", "")),
            "receivedDateBilling": str(st.session_state.get("receivedDateBilling", "")),
            "invoiceNumberBilling": st.session_state.get("invoiceNumberBilling", ""),
            "receivedByBilling": st.session_state.get("receivedByBilling", ""),
        },
        "requestForPaymentForm": {
            "receivedByRequest": st.session_state.get("receivedByRequest", ""),
            "refNo": st.session_state.get("refNo", ""),
            "receivedDateRequest": str(st.session_state.get("receivedDateRequest", "")),
            "refDate": str(st.session_state.get("refDate", "")),
            "rfpApproval": st.session_state.get("rfpApproval", ""),
            "rfpDate": str(st.session_state.get("rfpDate", "")),
            "rfpNo": st.session_state.get("rfpNo", ""),
        },
        "vendorForm": {
            "epoNo": st.session_state.get("epoNo", ""),
            "invoiceAmount": st.session_state.get("invoiceAmount", ""),
            "invoiceDate": str(st.session_state.get("invoiceDate", "")),
            "invoiceNo": st.session_state.get("invoiceNo", ""),
            "poDate": str(st.session_state.get("poDate", "")),
            "sentByandDate": st.session_state.get("sentByandDate", ""),
            "supplierName": st.session_state.get("supplierName", ""),
        }
    }
    # Only clear the state of the keys in all_data
    for section in all_data.values():
        for key in section.keys():
            if key in st.session_state:
                del st.session_state[key]
    return all_data
