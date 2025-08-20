import streamlit as st
from datetime import datetime
from functools import lru_cache

from api import delete_announcement, get_announcements, save_announcement

# Configure page
st.title("📢 Announcements Forum")

# Initialize session state
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

def toggle_form():
    st.session_state.show_form = not st.session_state.show_form

def change_page(change):
    st.session_state.current_page += change

# Cached function to get and process announcements
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_announcements():
    """Get announcements from Firebase with caching"""
    announcements = get_announcements() or {}
    processed = {}
    for ann_id, ann in announcements.items():
        processed_ann = ann.copy()
        try:
            processed_ann['datetime_obj'] = datetime.fromisoformat(ann.get('datetime_obj', ''))
        except (ValueError, TypeError):
            processed_ann['datetime_obj'] = datetime.now()
        processed[ann_id] = processed_ann
    return processed

# Cached function for filtering announcements
@st.cache_data(ttl=60)  # Cache for 1 minute
def get_filtered_announcements(announcements, search_title, search_author, search_tag, date_range):
    """Filter announcements with caching"""
    filtered = []
    for ann_id, ann in announcements.items():
        # Title filter
        if search_title and search_title.lower() not in ann.get("title", "").lower():
            continue
        # Author filter
        if search_author and search_author.lower() not in ann.get("author", "").lower():
            continue
        # Tag filter
        if search_tag:
            tags_lower = [t.lower() for t in ann.get("tags", [])]
            if search_tag.lower() not in tags_lower:
                continue
        # Date filter
        if date_range and len(date_range) == 2:
            ann_date = ann.get("datetime_obj")
            if ann_date:
                start, end = date_range
                if start == end:
                    if ann_date.date() != start:
                        continue
                else:
                    if not (start <= ann_date.date() <= end):
                        continue
        filtered.append((ann_id, ann))
    return filtered

# --- Search/filter section ---
with st.expander("🔎 Search & Filter Announcements", expanded=True):
    search_col1, search_col2, search_col3, search_col4 = st.columns([2, 2, 2, 3])
    with search_col1:
        search_title = st.text_input("Search by Title")
    with search_col2:
        search_author = st.text_input("Search by Author")
    with search_col3:
        search_tag = st.text_input("Search by Tag (single tag)")
    with search_col4:
        date_range = st.date_input(
            "Filter by Date Range", 
            [], 
            help="Select start and end date (optional)"
        )

# Header with post button
header_col1, header_col2 = st.columns([0.85, 0.15])
with header_col1:
    st.subheader("Recent Announcements")
with header_col2:
    st.button(
        "✍️ Post Announcement",
        on_click=toggle_form,
        key="show_form_btn",
        type="primary",
        use_container_width=True
    )

# Announcement form
if st.session_state.show_form:
    with st.form("announcement_form", clear_on_submit=True):
        st.markdown("### Create New Announcement")
        form_col1, form_col2 = st.columns(2)
        with form_col1:
            title = st.text_input("Title*", placeholder="Enter announcement title")
        with form_col2:
            author = st.text_input("Made by*", placeholder="Your name")
        content = st.text_area(
            "Content*", 
            placeholder="Write your announcement here...", 
            height=150
        )
        tags = st.text_input(
            "Tags (optional)", 
            placeholder="comma,separated,keywords", 
            help="Add relevant tags to help with searching"
        )
        submitted = st.form_submit_button(
            "📌 Post Announcement", 
            type="primary",
            use_container_width=True
        )
        if submitted:
            if not title:
                st.error("Title is required!")
            elif not content:
                st.error("Content is required!")
            elif not author:
                st.error("Author name is required!")
            else:
                announcement_data = {
                    "title": title,
                    "content": content,
                    "author": author,
                    "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                    "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                    "datetime_obj": datetime.now().isoformat()
                }
                announcement_id = f"ann_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                save_announcement(announcement_id, announcement_data)
                # Clear relevant caches
                get_cached_announcements.clear()
                get_filtered_announcements.clear()
                
                st.success("🎉 Announcement posted successfully!")
                st.balloons()
                st.session_state.show_form = False
                st.session_state.current_page = 1

# Get and process announcements with caching
announcements = get_cached_announcements()

# Filter announcements with caching
filtered_announcements = get_filtered_announcements(
    announcements, 
    search_title, 
    search_author, 
    search_tag, 
    date_range
)

# Sort announcements by datetime (newest first)
filtered_announcements.sort(key=lambda x: x[1]['datetime_obj'], reverse=True)

# Pagination settings
ITEMS_PER_PAGE = 5
total_pages = max(1, (len(filtered_announcements) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
st.session_state.current_page = min(st.session_state.current_page, total_pages)

# Display paginated announcements
start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
end_idx = start_idx + ITEMS_PER_PAGE
paginated_announcements = filtered_announcements[start_idx:end_idx]

if not paginated_announcements:
    st.markdown("---")
    st.markdown("#### No announcements found")
    st.caption("Try adjusting your search or filters.")
    st.markdown("---")
else:
    for ann_id, ann in paginated_announcements:
        with st.container():
            st.markdown("---")
            
            # Header row with title/author and date
            header_col1, header_col2 = st.columns([0.8, 0.2])
            with header_col1:
                st.markdown(f"#### {ann.get('title', 'Untitled')}")
                st.caption(f"Posted by: {ann.get('author', 'Anonymous')}")
            with header_col2:
                st.caption(ann.get('timestamp', ''))
            
            # Tags row
            if ann.get('tags'):
                st.write(" ".join([f"`{tag}`" for tag in ann['tags'][:8]]))
            
            # Content and delete button
            st.markdown(ann.get('content', ''))
            
            # Add delete button for admin (example implementation)
            if st.session_state.get('is_admin', False):  # You'll need to implement your auth logic
                if st.button(f"Delete {ann_id[:8]}...", key=f"del_{ann_id}"):
                    delete_announcement(ann_id)
                    # Clear caches after deletion
                    get_cached_announcements.clear()
                    get_filtered_announcements.clear()
                    st.rerun()

# Pagination controls
if len(filtered_announcements) > ITEMS_PER_PAGE:
    col1, col2, col3 = st.columns([0.2, 0.6, 0.2])
    
    with col1:
        if st.session_state.current_page > 1:
            st.button("⬅️ Previous", on_click=change_page, args=(-1,))
    
    with col2:
        st.markdown(f"<div style='text-align: center'>Page {st.session_state.current_page} of {total_pages}</div>", 
                   unsafe_allow_html=True)
    
    with col3:
        if st.session_state.current_page < total_pages:
            st.button("Next ➡️", on_click=change_page, args=(1,))

