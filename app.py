import streamlit as st
import pandas as pd

# ─────────────────────────────
# 🔐 Password gate (ask once)
# ─────────────────────────────
def require_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return

    st.title("🔐 Password Required")

    password = st.text_input(
        "Enter password",
        type="password",
        key="password_input"
    )

    if st.button("Unlock"):
        if password == st.secrets["auth"]["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")

    st.stop()


require_password()

# ─────────────────────────────
# Page config
# ─────────────────────────────
st.set_page_config(
    page_title="Enrollment & Waitlist Dashboard",
    layout="wide"
)

st.title("Enrollment & Waitlist Dashboard")

# ─────────────────────────────
# Load & clean data
# ─────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("Waitlist.csv")

    # Normalize column names
    df.columns = df.columns.str.strip()

    # Ensure numeric columns
    for col in ["Full Enrolments", "Number of Waitlists"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .replace({",": ""}, regex=True)
                .astype(float)
            )
        else:
            st.error(f"❌ '{col}' column not found in CSV")

    return df


df = load_data()

# ─────────────────────────────
# Sidebar filters (optional)
# ─────────────────────────────
st.sidebar.header("Filters (leave blank for all)")

venues = st.sidebar.multiselect(
    "Venue",
    options=sorted(df["Venue"].dropna().unique())
)

time_of_day = st.sidebar.multiselect(
    "Time of Day (AM / PM)",
    options=sorted(df["AM/PM"].dropna().unique())
)

start_times = st.sidebar.multiselect(
    "Start Time",
    options=sorted(df["Start Time"].dropna().unique())
)

# ─────────────────────────────
# Apply filters conditionally
# ─────────────────────────────
filtered_df = df.copy()

if venues:
    filtered_df = filtered_df[filtered_df["Venue"].isin(venues)]

if time_of_day:
    filtered_df = filtered_df[filtered_df["AM/PM"].isin(time_of_day)]

if start_times:
    filtered_df = filtered_df[filtered_df["Start Time"].isin(start_times)]

# ─────────────────────────────
# Metrics
# ─────────────────────────────
total_enrollment = filtered_df["Enrollment"].sum()
total_waitlist = filtered_df["Waitlist"].sum()

col1, col2 = st.columns(2)

with col1:
    st.metric("Total Enrollment", f"{int(total_enrollment):,}")

with col2:
    st.metric("Total Waitlist", f"{int(total_waitlist):,}")

# ─────────────────────────────
# Data preview
# ─────────────────────────────
st.subheader("Filtered Data")
st.dataframe(filtered_df, use_container_width=True)

# ─────────────────────────────
# Optional logout
# ─────────────────────────────
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()
