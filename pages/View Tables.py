import streamlit as st
import pandas as pd
import json
from api import get_records
import io

column_mapping = {
    "referenceNumber": "Ref No",
    "date": "Submission Date",
    "details": "Details",
    "pic": "PIC",
    "rfqDate": "RFQ Date",
    "vendorQuoteDate": "Vendor Quote Date",
    "quotationNumber": "Quote No",
    "quotationDate": "Quote Date",
    "prfbackOrder": "PRF/Back Order",
    "name": "Customer Name",
    "status": "Status",
    "customerPoNo": "Customer PO",
    "cpoDate": "PO Date",
    "epoNo": "Vendor PO",
    "poDate": "Vendor PO Date",
    "supplierName": "Supplier",
    "sentByandDate": "Sent By",
    "invoiceNo": "Vendor Invoice",
    "invoiceDate": "Invoice Date",
    "invoiceAmount": "Amount",
    "bofNo": "BOF No",
    "bofDate": "BOF Date",
    "bofApproval": "BOF Approval",
    "forInvoice": "Processing Status",
    "invoiceNumberBilling": "Billing Invoice",
    "invoiceDateBilling": "Billing Date",
    "receivedByBilling": "Billing Received By",
    "receivedDateBilling": "Billing Received Date",
    "rfpNo": "RFP No",
    "rfpDate": "RFP Date",
    "rfpApproval": "RFP Approval",
    "refNo": "RFP Ref No",
    "refDate": "RFP Ref Date",
    "receivedByRequest": "RFP Received By",
    "receivedDateRequest": "RFP Received Date"
}


# Configure page
st.title("📋 View Tables")
st.markdown("Easily browse, search, and filter your records.")


def flatten_data(data):
    """Flatten nested JSON structure into records."""
    if not data:
        return []

    records = []
    for ref_no, forms in data.items():
        row = {'referenceNumber': ref_no}
        for form in forms.values():
            if isinstance(form, dict):
                row.update(form)
        records.append(row)
    return records


def apply_filters(df, search_term, date_col, start_date, end_date):
    """Apply search and date filters to the DataFrame."""
    filtered_df = df.copy()

    # Apply search filter
    if search_term:
        search_term = search_term.lower()
        filtered_df = filtered_df[filtered_df.apply(
            lambda row: row.astype(str).str.lower(
            ).str.contains(search_term).any(),
            axis=1
        )]

    # Apply date filter if date column exists
    if date_col and date_col in filtered_df.columns and start_date and end_date:
        try:
            filtered_df[date_col] = pd.to_datetime(
                filtered_df[date_col], errors='coerce', dayfirst=True)
            filtered_df = filtered_df[
                (filtered_df[date_col] >= pd.to_datetime(start_date)) &
                (filtered_df[date_col] <= pd.to_datetime(end_date))
            ]
        except Exception as e:
            st.warning(f"Could not filter by date: {str(e)}")

    return filtered_df


def display_row_details(row):
    """Display full details of a row in a clean, readable format, with ability to hide."""
    st.markdown("---")
    with st.expander("🔍 Selected Record Details", expanded=True):
        # Map field names using column_mapping for display
        mapped_items = [
            (column_mapping.get(k, k), "N/A" if pd.isna(v) else v)
            for k, v in row.items()
        ]
        details_df = pd.DataFrame(mapped_items, columns=["Field", "Value"])
        # Convert all values to string to avoid pyarrow error
        details_df["Value"] = details_df["Value"].apply(
            lambda v: v.strftime("%Y-%m-%d") if hasattr(v, "strftime") else str(v)
        )
        st.dataframe(
            details_df.style.set_properties(**{
                'background-color': '#f9f9f9',
                'color': '#333',
                'border-color': '#e0e0e0',
                'font-size': '16px'
            }).hide(axis="index"),
            use_container_width=True,
            hide_index=True,
            height=min(600, len(details_df) * 38 + 38)
        )


def main():
    # Initialize session state
    if "page_num" not in st.session_state:
        st.session_state.page_num = 1
    if "selected_row" not in st.session_state:
        st.session_state.selected_row = None

    # Load and process data
    @st.cache_data(show_spinner="Loading records...", ttl=600)
    def load_data():
        return get_records(form_type="New Reference")
    data = load_data()
    if data is None:
        return

    records = flatten_data(data)[::-1]
    if not records:
        st.warning("No records found in the data.")
        return

    # Define the desired column order and display names
    desired_columns = [
        "referenceNumber", "name", "date", "details", "pic", "rfqDate", "vendorQuoteDate",
        "quotationNumber", "quotationDate", "prfbackOrder", "status", "customerPoNo", "cpoDate",
        "epoNo", "poDate", "supplierName", "sentByandDate", "invoiceNo", "invoiceDate", "invoiceAmount",
        "bofNo", "bofDate", "bofApproval", "forInvoice", "invoiceNumberBilling", "invoiceDateBilling",
        "receivedByBilling", "receivedDateBilling", "rfpNo", "rfpDate", "rfpApproval", "refNo",
        "refDate", "receivedByRequest", "receivedDateRequest"
    ]

    # Create DataFrame and reorder columns
    df = pd.DataFrame(records)
    # Only keep columns that exist in the DataFrame
    df = df[[col for col in desired_columns if col in df.columns]]

    # Sidebar for filters
    with st.sidebar:
        st.header("Filters")

        # Search bar
        search_term = st.text_input("Search records")

        # Date filter
        date_cols = [col for col in df.columns if 'date' in col.lower()]
        date_col = None
        start_date = None
        end_date = None

        if date_cols:
            # Map original date columns to their display names using column_mapping
            date_col_options = ['Default'] + \
                [column_mapping.get(col, col) for col in date_cols]
            selected_display_col = st.selectbox(
                "Date column",
                options=date_col_options,
                help="Select a column to filter by date range"
            )
            # Map back from display name to original column name
            if selected_display_col != 'Default':
                # Reverse mapping: find the original column name
                for orig_col, display_col in column_mapping.items():
                    if display_col == selected_display_col:
                        date_col = orig_col
                        break
                else:
                    date_col = selected_display_col  # fallback if not found in mapping
            else:
                date_col = None

            if date_col and date_col != 'Default':
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start date")
                with col2:
                    end_date = st.date_input("End date")

                if start_date and end_date and start_date > end_date:
                    st.warning("Start date must be before end date")

    # Apply filters
    filtered_df = apply_filters(
        df, search_term, date_col, start_date, end_date)

    # Pagination settings
    PAGE_SIZE = 10
    total_pages = max(1, (len(filtered_df) + PAGE_SIZE - 1) // PAGE_SIZE)
    current_page = st.session_state.page_num

    # Ensure current page is within valid range
    if current_page > total_pages:
        st.session_state.page_num = total_pages
        current_page = total_pages

    # Display record count
    st.markdown(f"**Total records: {len(filtered_df)}**")

    # Pagination controls
    col1, col2, col3, col4 = st.columns([2, 2, 1, 2])
    with col2:
        if st.button("⬅️ Previous", disabled=current_page <= 1):
            st.session_state.page_num = max(1, current_page - 1)
    with col3:
        if st.button("Next ➡️", disabled=current_page >= total_pages):
            st.session_state.page_num = min(total_pages, current_page + 1)

    # Show current page data
    start = (current_page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    current_page_data = filtered_df.iloc[start:end].copy()
    current_page_data_display = current_page_data.rename(
        columns=column_mapping)

    # Display the data with selection
    st.markdown("**Hover over a row and click to view details**")
    selected_index = st.dataframe(
        current_page_data_display,
        use_container_width=True,
        height=min(600, (PAGE_SIZE + 1) * 35),
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True
    )

    # Store selected row in session state
    if selected_index.selection.rows:
        selected_row_index = selected_index.selection.rows[0]
        st.session_state.selected_row = current_page_data.iloc[selected_row_index].to_dict(
        )
    st.markdown(f"**Page {current_page} of {total_pages}**",
                unsafe_allow_html=True)
    if st.session_state.selected_row:
        display_row_details(st.session_state.selected_row)

    # Download button for filtered table as XLSX
    output = io.BytesIO()
    filtered_df.rename(columns=column_mapping).to_excel(output, index=False, engine='openpyxl')
    st.download_button(
        label="⬇️ Download Table as XLSX",
        data=output.getvalue(),
        file_name="smart_sourcing_records.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


main()
