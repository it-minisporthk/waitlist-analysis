import streamlit as st
import pandas as pd
import os

# ─────────────────────────────
# 🔐 Password gate — comment out the call below to disable locally
# ─────────────────────────────
def require_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return

    st.title("🔐 Password Required")

    password = st.text_input("Enter password", type="password", key="password_input")

    if st.button("Unlock"):
        if password == st.secrets["auth"]["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")

    st.stop()

# require_password()   # ← keep commented for local runs

# ─────────────────────────────
# Page config
# ─────────────────────────────
st.set_page_config(page_title="Enrollment & Waitlist Dashboard", layout="wide")
st.title("Enrollment & Waitlist Dashboard")

# ─────────────────────────────
# Load & clean data
# ─────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("Waitlist.csv")
    df.columns = df.columns.str.strip()

    for col in ["Full Enrolments", "Number of Waitlists", "Total (including waitlist)"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(",", "", regex=False).astype(float)
        else:
            st.error(f"❌ Column '{col}' not found in CSV")

    return df

df = load_data()

# ─────────────────────────────
# Sidebar filters
# ─────────────────────────────
st.sidebar.header("Filters (leave blank for all)")

terms = st.sidebar.multiselect("Term", options=sorted(df["Term"].dropna().unique()))
venues = st.sidebar.multiselect("Venue", options=sorted(df["Venue"].dropna().unique()))
time_of_day = st.sidebar.multiselect("Time of Day (AM / PM)", options=sorted(df["AM/PM"].dropna().unique()))
start_times = st.sidebar.multiselect("Start Time", options=sorted(df["Start Time"].dropna().unique()))

show_high_demand_only = st.sidebar.checkbox("Show high-demand classes only", value=False,
                                            help="Only display classes where waitlist > enrolments")

# ─────────────────────────────
# Apply filters step by step
# ─────────────────────────────
filtered_df = df.copy()

if venues:
    filtered_df = filtered_df[filtered_df["Venue"].isin(venues)]
if time_of_day:
    filtered_df = filtered_df[filtered_df["AM/PM"].isin(time_of_day)]
if start_times:
    filtered_df = filtered_df[filtered_df["Start Time"].isin(start_times)]
if terms:
    filtered_df = filtered_df[filtered_df["Term"].isin(terms)]

# ─────────────────────────────
# Apply high-demand toggle (after other filters)
# ─────────────────────────────
display_df = filtered_df.copy()

if show_high_demand_only:
    if "Full Enrolments" in display_df.columns and "Number of Waitlists" in display_df.columns:
        display_df = display_df[display_df["Number of Waitlists"] > display_df["Full Enrolments"]]
    else:
        st.sidebar.warning("High-demand filter unavailable — missing columns")

# ─────────────────────────────
# Metrics — based on final display_df
# ─────────────────────────────
total_enrollment = display_df["Full Enrolments"].sum()
total_waitlist   = display_df["Number of Waitlists"].sum()
total_enrollment_waitlist_included = display_df["Total (including waitlist)"].sum()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Full Enrollment", f"{int(round(total_enrollment)):,}")
with col2:
    st.metric("Total Waitlist", f"{int(round(total_waitlist)):,}")
with col3:
    st.metric("Total (including waitlist)", f"{int(round(total_enrollment_waitlist_included)):,}")

# ─────────────────────────────
# Data preview with highlighting + integer display
# ─────────────────────────────
st.subheader("Filtered Data" + (" – High Demand Only" if show_high_demand_only else ""))

# Ensure integer display
for col in ["Full Enrolments", "Number of Waitlists", "Total (including waitlist)"]:
    if col in display_df.columns:
        display_df[col] = display_df[col].round(0).astype("Int64")

def highlight_high_waitlist(row):
    if pd.notna(row["Number of Waitlists"]) and pd.notna(row["Full Enrolments"]):
        if row["Number of Waitlists"] > row["Full Enrolments"]:
            return ["background-color: #ffcccc"] * len(row)
    return [""] * len(row)

if "Full Enrolments" in display_df.columns and "Number of Waitlists" in display_df.columns:
    styled_df = display_df.style.apply(highlight_high_waitlist, axis=1)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
else:
    st.dataframe(display_df, use_container_width=True)

st.caption("🔴 Rows in red: Waitlist > Full Enrolments (high demand)")

# Logout button if password active
if "authenticated" in st.session_state and st.session_state.authenticated:
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
