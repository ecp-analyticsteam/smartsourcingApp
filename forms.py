import streamlit as st
import datetime
import api
from data_management import save_all_data
from firebase_config import get_firestore
import pandas as pd


def safe_date_input(label, key, form_data, default=None):
    """Safe date input with fallback to today"""
    default = None
    if not form_data or key not in form_data:
        return st.date_input(label, key=key, value=default)

    date_value = form_data[key]
    if isinstance(date_value, datetime.date):
        return st.date_input(label, key=key, value=date_value)
    if isinstance(date_value, str):
        try:
            parsed_date = datetime.datetime.strptime(
                date_value, "%Y-%m-%d").date()
            return st.date_input(label, key=key, value=parsed_date)
        except ValueError:
            pass
    return st.date_input(label, key=key, value=default)


firestore_db = get_firestore()


def update_reference_type():
    st.session_state.referenceType = st.session_state.referenceType_select


# Load customer data from Excel
customer_df = pd.read_excel('./pics/Customer Data.xlsx')
customer_names = customer_df['CUSTOMER NAME'].dropna().unique().tolist()


def deploy_forms(form_data):

    latest_ref = api.get_latest_reference_number()
    aftersales_latest_ref = api.get_latest_aftersales_reference_number()

    col_ref1, col_ref2 = st.columns(2)
    with col_ref1:
        st.markdown("**:orange[Latest Ref]**")
        st.code(latest_ref, language="text")
    with col_ref2:
        st.markdown("**:orange[Latest After Sales Ref]**")
        st.code(aftersales_latest_ref, language="text")

    """Render all form sections in a more compact, user-friendly layout."""
    with st.form("allForms", clear_on_submit=True, border=False, enter_to_submit=False):
        with st.expander("👤 Customer Details", expanded=True):
            # Row 1: Reference Number, Date, Details, PIC
            c1_r1, c2_r1, c3_r1, c4_r1 = st.columns([1, 1, 2, 1])
            with c1_r1:
                st.text_input(
                    "Reference Number",
                    key="referenceNumber",
                    value=form_data.get("customerForm", {}).get("referenceNumber", "").upper(),
                    placeholder="Enter reference number"
                )
           #  "Submission Date"
            with c2_r1: 
                st.date_input(
                    "Submission Date",
                    value=(
                        form_data.get("customerForm", {}).get("date", datetime.date.today())
                        if st.session_state.form_mode == "edit"
                        else datetime.date.today()
                    ),
                    key="date"
                )
            with c3_r1:
                st.text_input(
                    "Details",
                    value=form_data.get("customerForm", {}).get("details", ""),
                    key="details",
                    placeholder="Enter details"
                )
            with c4_r1:
                user_ref = firestore_db.collection('users').document(
                    st.session_state.current_user['uid'])
                user_data = user_ref.get().to_dict()
                user_name = user_data.get('first_name')
                st.text_input(
                    "Person in Charge (PIC)",
                    value=form_data.get("customerForm", {}).get("pic", user_name),
                    key="pic",
                    placeholder="Person in charge"
                )

            # Row 2: RFQ Date, Vendor Quote Date, Quotation Number, Quotation Date
            c1_r2, c2_r2, c3_r2, c4_r2 = st.columns(4)
            with c1_r2:
                safe_date_input(
                    "RFQ Date",
                    "rfqDate",
                    form_data.get("customerForm", {})
                )
            with c2_r2:
                safe_date_input(
                    "Vendor Quote Date",
                    "vendorQuoteDate",
                    form_data.get("customerForm", {})
                )
            with c3_r2:
                st.text_input(
                    "Quotation Number",
                    value=form_data.get("customerForm", {}).get("quotationNumber", ""),
                    key="quotationNumber",
                    placeholder="Enter quotation number"
                )
            with c4_r2:
                safe_date_input(
                    "Quotation Date",
                    "quotationDate",
                    form_data.get("customerForm", {})
                )

            # Row 3: PRF/Back Order, Customer Name
            c1_r3, c2_r3 = st.columns(2)
            with c1_r3:
                st.text_input(
                    "PRF/Back Order",
                    value=form_data.get("customerForm", {}).get("prfbackOrder", ""),
                    key="prfbackOrder",
                    placeholder="Enter PRF back order"
                )
            with c2_r3:
                st.selectbox(
                    "Customer Name",
                    options=customer_names,
                    index=customer_names.index(form_data.get("customerForm", {}).get("name", "")) if form_data.get(
                        "customerForm", {}).get("name", "") in customer_names else None,
                    placeholder="Select or enter a customer name",
                    key="name",
                    accept_new_options=True,
                )

            # Row 4: Customer PO No, CPO Date, Customer Status
            c1_r4, c2_r4, c3_r4 = st.columns(3)
            with c1_r4:
                st.text_input(
                    "Customer PO No",
                    value=form_data.get("customerForm", {}).get("customerPoNo", ""),
                    key="customerPoNo",
                    placeholder="Enter customer PO number"
                )
            with c2_r4:
                safe_date_input(
                    "CPO Date",
                    "cpoDate",
                    form_data.get("customerForm", {})
                )
            with c3_r4:
                st.selectbox(
                    "Customer Status",
                    options=[
                        "Open",
                        "QV",
                        "QC",
                        "POC",
                        "POV",
                        "DV",
                        "DC",
                        "BOF",
                        "RFP",
                        "Closed",
                        "Cancelled"
                    ],
                    index=[
                        "Open",
                        "QV",
                        "QC",
                        "POC",
                        "POV",
                        "DV",
                        "DC",
                        "BOF",
                        "RFP",
                        "Closed",
                        "Cancelled"
                    ].index(form_data.get("customerForm", {}).get("status", "Open"))
                    if form_data.get("customerForm", {}).get("status", "Open") in [
                        "Open",
                        "QV",
                        "QC",
                        "POC",
                        "POV",
                        "DV",
                        "DC",
                        "BOF",
                        "RFP",
                        "Closed",
                        "Cancelled"
                    ] else 0,
                    key="status",
                    placeholder="Select status"
                )

        # --- Vendor Form Section ---
        with st.expander("🏢 Vendor Details", expanded=False):
            # Row 1: EPO No, PO Date
            v1_r1, v2_r1 = st.columns(2)
            with v1_r1:
                st.text_input(
                    "EPO No",
                    value=form_data.get("vendorForm", {}).get("epoNo", ""),
                    key="epoNo",
                    placeholder="Enter EPO number"
                )
            with v2_r1:
                safe_date_input("PO Date", "poDate",
                                form_data.get("vendorForm", {}))

            # Row 2: Supplier Name, Sent By and Date
            v1_r2, v2_r2 = st.columns(2)
            with v1_r2:
                st.text_input(
                    "Supplier Name",
                    value=form_data.get("vendorForm", {}).get(
                        "supplierName", ""),
                    key="supplierName",
                    placeholder="Enter supplier name"
                )
            with v2_r2:
                st.text_input(
                    "Sent By and Date",
                    value=form_data.get("vendorForm", {}).get(
                        "sentByandDate", ""),
                    key="sentByandDate",
                    placeholder="Enter sender and date"
                )

            # Row 3: Invoice No, Invoice Date, Invoice Amount
            v1_r3, v2_r3, v3_r3 = st.columns(3)
            with v1_r3:
                st.text_input(
                    "Invoice No",
                    value=form_data.get("vendorForm", {}).get("invoiceNo", ""),
                    key="invoiceNo",
                    placeholder="Enter invoice number"
                )
            with v2_r3:
                safe_date_input("Invoice Date", "invoiceDate",
                                form_data.get("vendorForm", {}))
            with v3_r3:
                st.text_input(
                    "Invoice Amount",
                    value=form_data.get("vendorForm", {}).get(
                        "invoiceAmount", ""),
                    key="invoiceAmount",
                    placeholder="Enter invoice amount"
                )
        # --- Billing Order Form Section ---
        with st.expander("📄 Billing Order", expanded=False):
            # Row 1: BOF No, BOF Date, BOF Approval
            b1_r1, b2_r1, b3_r1 = st.columns(3)
            with b1_r1:
                st.text_input(
                    "BOF No",
                    value=form_data.get("billingOrderForm",
                                        {}).get("bofNo", ""),
                    key="bofNo",
                    placeholder="Enter BOF number"
                )
            with b2_r1:
                safe_date_input("BOF Date", "bofDate",
                                form_data.get("billingOrderForm", {}))
            with b3_r1:
                st.text_input(
                    "BOF Approval",
                    value=form_data.get("billingOrderForm", {}).get(
                        "bofApproval", ""),
                    key="bofApproval",
                    placeholder="Enter BOF approval"
                )

            # Row 2: For Invoice, Invoice Number Billing
            b1_r2, b2_r2 = st.columns(2)
            with b1_r2:
                st.text_input(
                    "For Invoice Processing",
                    value=form_data.get("billingOrderForm", {}).get(
                        "forInvoice", ""),
                    key="forInvoice",
                    placeholder="Enter invoice details"
                )
            with b2_r2:
                st.text_input(
                    "Invoice Number Billing",
                    value=form_data.get("billingOrderForm", {}).get(
                        "invoiceNumberBilling", ""),
                    key="invoiceNumberBilling",
                    placeholder="Enter invoice number"
                )

            # Row 3: Invoice Date Billing, Received By, Received Date
            b1_r3, b2_r3, b3_r3 = st.columns(3)
            with b1_r3:
                safe_date_input("Invoice Date Billing", "invoiceDateBilling",
                                form_data.get("billingOrderForm", {}))
            with b2_r3:
                st.text_input(
                    "Received By",
                    value=form_data.get("billingOrderForm", {}).get(
                        "receivedByBilling", ""),
                    key="receivedByBilling",
                    placeholder="Enter receiver name"
                )
            with b3_r3:
                safe_date_input("Received Date", "receivedDateBilling",
                                form_data.get("billingOrderForm", {}))

        # --- Request For Payment Form Section ---
        with st.expander("💵 Request For Payment", expanded=False):
            # Row 1: RFP No., RFP Date, RFP Approval
            r1_c1, r1_c2, r1_c3 = st.columns(3)
            with r1_c1:
                st.text_input(
                    "RFP No",
                    value=form_data.get("requestForPaymentForm", {}).get("rfpNo", ""),
                    key="rfpNo",
                    placeholder="Enter RFP number"
                )
            with r1_c2:
                safe_date_input(
                    "RFP Date",
                    "rfpDate",
                    form_data.get("requestForPaymentForm", {})
                )
            with r1_c3:
                st.text_input(
                    "RFP Approval",
                    value=form_data.get("requestForPaymentForm", {}).get("rfpApproval", ""),
                    key="rfpApproval",
                    placeholder="Enter RFP approval"
                )

            # Row 2: For Payment Processing, Ref. No., Ref. Date
            r2_c1, r2_c2 = st.columns(2)
            with r2_c1:
                st.text_input(
                    "Ref No",
                    value=form_data.get("requestForPaymentForm", {}).get("refNo", ""),
                    key="refNo",
                    placeholder="Enter reference number"
                )
            with r2_c2:
               safe_date_input(
                    "Ref Date",
                    "refDate",
                    form_data.get("requestForPaymentForm", {})
                )

            # Row 3: Ref. Date, Received By, Received Date
            r3_c2, r3_c3 = st.columns(2)                
            with r3_c2:
                st.text_input(
                    "Received By",
                    value=form_data.get("requestForPaymentForm", {}).get("receivedBy", ""),
                    key="receivedBy",
                    placeholder="Enter receiver name"
                )
            with r3_c3:
                safe_date_input(
                    "Received Date",
                    "receivedDate",
                    form_data.get("requestForPaymentForm", {})
                )
        submitted = st.form_submit_button("✅ Save All Forms")

        if st.session_state.form_mode == "new":
            if submitted:
                st.toast("All Forms saved!", icon="🔥")
                handle_form_submission("Create")
                st.rerun()
        else:
            if st.session_state.record_found:
                if submitted:
                    st.toast("All Forms edited!", icon="🔥")
                    handle_form_submission(type="Edit")
                    st.rerun()


def handle_form_submission(type):
    if "referenceType" not in st.session_state or not st.session_state.referenceType:
        st.error(
            "Reference Type is missing. Please select a Reference Type before submitting.")
        return

    print("Reference Type in Handle forms:", st.session_state.referenceType)
    form_type = st.session_state.referenceType
    all_data = save_all_data()
    customer_form = all_data.get("customerForm", {})
    reference_number = customer_form.get("referenceNumber", "unknown")
    api.save_record(reference_number, all_data, form_type, type)
