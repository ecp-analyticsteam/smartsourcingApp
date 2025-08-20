import streamlit as st
import json
from datetime import datetime
import math

from api import get_logs


# Load JSON data
def load_logs(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

# Extract relevant data per reference number
def get_reference_actions(data):
    actions = []
    for _, entry in data.items():
        ref_no = entry.get("referenceNumber")
        pic = entry.get("changedDetails", {}).get("customerForm", {}).get("pic", "")
        action = entry.get("action", "")
        timestamp = entry.get("timestamp", "")
        user = entry.get("user", {}).get("displayName", "")
        if ref_no and timestamp:
            actions.append({
                "referenceNumber": ref_no,
                "action": action,
                "pic": pic,
                "timestamp": timestamp,
                "user": user,
                "details": entry
            })
    # Sort actions by timestamp (latest first)
    actions.sort(key=lambda x: x["timestamp"], reverse=True)
    return actions

# Format timestamp
def format_timestamp(ts):
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %I:%M %p")
    except:
        return ts

# Main Streamlit app
def main():
    st.title("🔔 PIC Action Notifications")

    data = get_logs()
    actions = get_reference_actions(data)

    # --- Search box ---
    search_query = st.text_input("🔍 Search by Reference #, PIC, Action, or User", "")
    if search_query:
        query = search_query.lower()
        actions = [
            a for a in actions
            if query in str(a["referenceNumber"]).lower()
            or query in str(a["pic"]).lower()
            or query in str(a["action"]).lower()
            or query in str(a["user"]).lower()
        ]

    # Pagination settings
    items_per_page = 10
    total_items = len(actions)
    total_pages = max(1, math.ceil(total_items / items_per_page))

    st.subheader(f"📋 Recent PIC Actions (Total: {total_items})")

    # Page navigator using Next/Previous buttons
    if "page" not in st.session_state:
        st.session_state.page = 1

    # Reset to page 1 only if the search query has changed
    if "last_search_query" not in st.session_state:
        st.session_state.last_search_query = ""
    if search_query != st.session_state.last_search_query:
        st.session_state.page = 1
        st.session_state.last_search_query = search_query

    prev_disabled = st.session_state.page <= 1
    next_disabled = st.session_state.page >= total_pages
    page = st.session_state.page

    # Place Previous and Next buttons in a single row, each filling its column
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Previous", use_container_width=True, disabled=(page == 1)):
            if st.session_state.page > 1:
                st.session_state.page -= 1
    with col2:
        if st.button("Next ➡️", use_container_width=True, disabled=next_disabled):
            
            if st.session_state.page < total_pages:
                st.session_state.page += 1


    # Determine which items to display
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_actions = actions[start_idx:end_idx]

    for action in paginated_actions:
        st.info(
            f"**[{action['pic'].upper()}]** performed **{action['action']}** "
            f"on **Reference #{action['referenceNumber']}**\n\n"
            f"🕒 {format_timestamp(action['timestamp'])} by {action['user']}",
            icon="📌"
        )
        with st.expander("View Full Details"):
            st.json(action["details"])

    st.markdown(f"Page **{page}** of **{total_pages}**")

main()
