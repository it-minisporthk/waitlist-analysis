import streamlit as st
import pandas as pd

# ─────────────────────────────
# 🔐 Password protection (password only, once per session)
# ─────────────────────────────
def require_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return

    st.title("🔐 Password Required")

    password = st.text_input("Enter password", type="password")

    if st.button("Unlock"):
        if password == st.secrets["auth"]["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")

    st.stop()

# 🔴 Uncomment this when deploying
# require_password()

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
    df.columns = df.columns.str.strip()

    # Normalize Day of Week (CRITICAL FIX)
    if "Day of Week" in df.columns:
        df["Day of Week"] = (
            df["Day of Week"]
            .astype(str)
            .str.strip()
            .str.title()
        )

    # Clean numeric columns
    numeric_cols = [
        "Full Enrolments",
        "Number of Waitlists",
        "Total (including waitlist)"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .astype(float)
            )
        else:
            st.error(f"❌ Missing required column: {col}")

    return df

df = load_data()

# ─────────────────────────────
# Sidebar filters
# ─────────────────────────────
st.sidebar.header("Filters (leave blank for all)")

venues = st.sidebar.multiselect(
    "Venue",
    options=sorted(df["Venue"].dropna().unique())
)

# ✅ Ordered Day of Week filter (Mon → Sun)
WEEKDAY_ORDER = [
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat",
    "Sun",
]

available_days = df["Day of Week"].dropna().unique()
ordered_days = [d for d in WEEKDAY_ORDER if d in available_days]

days_of_week = st.sidebar.multiselect(
    "Day of Week",
    options=ordered_days
)

time_of_day = st.sidebar.multiselect(
    "Time of Day (AM / PM)",
    options=sorted(df["AM/PM"].dropna().unique())
)

start_times = st.sidebar.multiselect(
    "Start Time",
    options=sorted(df["Start Time"].dropna().unique())
)

show_high_demand_only = st.sidebar.checkbox(
    "Show high-demand classes only",
    help="Waitlist greater than full enrolments"
)

# ─────────────────────────────
# Apply filters
# ─────────────────────────────
filtered_df = df.copy()

if venues:
    filtered_df = filtered_df[filtered_df["Venue"].isin(venues)]

if days_of_week:
    filtered_df = filtered_df[filtered_df["Day of Week"].isin(days_of_week)]

if time_of_day:
    filtered_df = filtered_df[filtered_df["AM/PM"].isin(time_of_day)]

if start_times:
    filtered_df = filtered_df[filtered_df["Start Time"].isin(start_times)]

# High-demand filter
if show_high_demand_only:
    filtered_df = filtered_df[
        filtered_df["Number of Waitlists"] > filtered_df["Full Enrolments"]
    ]

# ─────────────────────────────
# Metrics
# ─────────────────────────────
total_enrolment = filtered_df["Full Enrolments"].sum()
total_waitlist = filtered_df["Number of Waitlists"].sum()
total_combined = filtered_df["Total (including waitlist)"].sum()

col1, col2, col3 = st.columns(3)

col1.metric("Full Enrolments", f"{int(total_enrolment):,}")
col2.metric("Waitlist", f"{int(total_waitlist):,}")
col3.metric("Total (Including Waitlist)", f"{int(total_combined):,}")

# ─────────────────────────────
# Table display
# ─────────────────────────────
st.subheader(
    "Filtered Classes"
    + (" — High Demand Only" if show_high_demand_only else "")
)

# Format numeric columns as integers
for col in [
    "Full Enrolments",
    "Number of Waitlists",
    "Total (including waitlist)"
]:
    filtered_df[col] = filtered_df[col].round(0).astype("Int64")

def highlight_high_demand(row):
    if row["Number of Waitlists"] > row["Full Enrolments"]:
        return ["background-color: #ffcccc"] * len(row)
    return [""] * len(row)

styled_df = filtered_df.style.apply(highlight_high_demand, axis=1)

st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True
)

st.caption("🔴 Highlighted rows indicate waitlist exceeds enrolments")

# ─────────────────────────────
# Logout (only active when password enabled)
# ─────────────────────────────
if "authenticated" in st.session_state and st.session_state.authenticated:
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
