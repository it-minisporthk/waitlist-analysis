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

# 🔴 Uncomment when deploying
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

    # Normalize Day of Week
    if "Day of Week" in df.columns:
        df["Day of Week"] = (
            df["Day of Week"]
            .astype(str)
            .str.strip()
            .str.title()
        )

    # Clean numeric columns
    numeric_cols = [
        "Quota",
        "Full Enrolments",
        "Number of Waitlists",
        "Total (including waitlist)",
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
# Sidebar filters (ORDERED)
# ─────────────────────────────
st.sidebar.header("Filters (leave blank for all)")

terms = st.sidebar.multiselect(
    "Term",
    sorted(df["Term"].dropna().unique())
)

venues = st.sidebar.multiselect(
    "Venue",
    sorted(df["Venue"].dropna().unique())
)

# Day of Week (Mon → Sun, never disabled)
WEEKDAY_ORDER = {
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6,
    "Sunday": 7,
}

available_days = (
    df["Day of Week"]
    .dropna()
    .astype(str)
    .str.strip()
    .str.title()
    .unique()
)

ordered_days = sorted(
    available_days,
    key=lambda d: WEEKDAY_ORDER.get(d, 99)
)

days_of_week = st.sidebar.multiselect(
    "Day of Week",
    ordered_days
)

time_of_day = st.sidebar.multiselect(
    "Time of Day (AM / PM)",
    sorted(df["AM/PM"].dropna().unique())
)

start_times = st.sidebar.multiselect(
    "Start Time",
    sorted(df["Start Time"].dropna().unique())
)

coaches = st.sidebar.multiselect(
    "Coach",
    sorted(df["Coach"].dropna().unique())
)

show_high_demand_only = st.sidebar.checkbox(
    "Show high-demand classes only",
    help="Waitlist greater than full enrolments"
)

# ─────────────────────────────
# Apply filters
# ─────────────────────────────
filtered_df = df.copy()

if terms:
    filtered_df = filtered_df[filtered_df["Term"].isin(terms)]

if venues:
    filtered_df = filtered_df[filtered_df["Venue"].isin(venues)]

if days_of_week:
    filtered_df = filtered_df[filtered_df["Day of Week"].isin(days_of_week)]

if time_of_day:
    filtered_df = filtered_df[filtered_df["AM/PM"].isin(time_of_day)]

if start_times:
    filtered_df = filtered_df[filtered_df["Start Time"].isin(start_times)]

if coaches:
    filtered_df = filtered_df[filtered_df["Coach"].isin(coaches)]

if show_high_demand_only:
    filtered_df = filtered_df[
        filtered_df["Number of Waitlists"] > filtered_df["Full Enrolments"]
    ]

# ─────────────────────────────
# Metrics
# ─────────────────────────────
total_enrolments = filtered_df["Full Enrolments"].sum()
total_waitlist = filtered_df["Number of Waitlists"].sum()
total_combined = filtered_df["Total (including waitlist)"].sum()
total_quota = filtered_df["Quota"].sum()

utilization_pct = (
    (total_enrolments / total_quota) * 100
    if total_quota > 0
    else 0
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Full Enrolments", f"{int(total_enrolments):,}")
col2.metric("Waitlist", f"{int(total_waitlist):,}")
col3.metric("Total (Including Waitlist)", f"{int(total_combined):,}")
col4.metric("Utilization %", f"{utilization_pct:.2f}%")

# ─────────────────────────────
# Table display
# ─────────────────────────────
st.subheader(
    "Filtered Classes"
    + (" — High Demand Only" if show_high_demand_only else "")
)

DISPLAY_COLUMNS = [
    "Term",
    "Venue",
    "Day of Week",
    "AM/PM",
    "Start Time",
    "Coach",
    "Quota",
    "Full Enrolments",
    "Number of Waitlists",
    "Total (including waitlist)",
]

display_df = filtered_df[DISPLAY_COLUMNS].copy()

# Per-class utilization
display_df["Utilization %"] = (
    (display_df["Full Enrolments"] / display_df["Quota"]) * 100
)

# Format integer columns
for col in [
    "Quota",
    "Full Enrolments",
    "Number of Waitlists",
    "Total (including waitlist)",
]:
    display_df[col] = display_df[col].round(0).astype("Int64")

def highlight_high_demand(row):
    if row["Number of Waitlists"] > row["Full Enrolments"]:
        return ["background-color: #ffcccc"] * len(row)
    return [""] * len(row)

styled_df = display_df.style.apply(highlight_high_demand, axis=1)

# ✅ Force 2-decimal display for Utilization %
styled_df = styled_df.format({
    "Utilization %": "{:.2f}"
})

st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True
)

st.caption("🔴 Highlighted rows indicate waitlist exceeds enrolments")

# ─────────────────────────────
# Logout
# ─────────────────────────────
if "authenticated" in st.session_state and st.session_state.authenticated:
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
