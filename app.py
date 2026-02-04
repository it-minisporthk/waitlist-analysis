import streamlit as st
import pandas as pd

# ---------- Page Config ----------
st.set_page_config(page_title="Waitlist Analysis", layout="wide")

# ---------- Load Data ----------
@st.cache_data
def load_data():
    return pd.read_csv("Waitlist.csv")

df = load_data()

# ---------- Sidebar Filters ----------
st.sidebar.header("Filters")

term_filter = st.sidebar.multiselect("Term", sorted(df["Term"].dropna().unique()))
venue_filter = st.sidebar.multiselect("Venue", sorted(df["Venue"].dropna().unique()))
day_filter = st.sidebar.multiselect("Day of Week", sorted(df["Day of Week"].dropna().unique()))
ampm_filter = st.sidebar.multiselect("Time of Day (AM/PM)", sorted(df["AM/PM"].dropna().unique()))
start_time_filter = st.sidebar.multiselect("Start Time", sorted(df["Start Time"].dropna().unique()))
coach_filter = st.sidebar.multiselect("Coach", sorted(df["Coach"].dropna().unique()))

# New Filters
age_options = ["All"] + sorted(df["Age"].dropna().astype(str).unique().tolist())
age_filter = st.sidebar.selectbox("Age", age_options)

high_demand_only = st.sidebar.toggle("Show High-Demand Classes (Waitlist > Quota)", value=False)

# ---------- Apply Filters ----------
filtered_df = df.copy()

if term_filter:
    filtered_df = filtered_df[filtered_df["Term"].isin(term_filter)]

if venue_filter:
    filtered_df = filtered_df[filtered_df["Venue"].isin(venue_filter)]

if day_filter:
    filtered_df = filtered_df[filtered_df["Day of Week"].isin(day_filter)]

if ampm_filter:
    filtered_df = filtered_df[filtered_df["AM/PM"].isin(ampm_filter)]

if start_time_filter:
    filtered_df = filtered_df[filtered_df["Start Time"].isin(start_time_filter)]

if coach_filter:
    filtered_df = filtered_df[filtered_df["Coach"].isin(coach_filter)]

if age_filter != "All":
    filtered_df = filtered_df[filtered_df["Age"].astype(str) == age_filter]

if high_demand_only:
    filtered_df = filtered_df[filtered_df["Number of Waitlists"] > filtered_df["Quota"]]

# ---------- KPIs ----------
full_enrollments = filtered_df["Full Enrolments"].sum()
waitlist = filtered_df["Number of Waitlists"].sum()
total_including_waitlist = filtered_df["Total (including waitlist)"].sum()
quota = filtered_df["Quota"].sum()

utilization_pct = 0
if quota > 0:
    utilization_pct = (full_enrollments / quota) * 100

# ---------- Title ----------
st.title("Waitlist Analysis")

# ---------- Top Stats ----------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Full Enrollments", f"{int(full_enrollments):,}")
col2.metric("Waitlist", f"{int(waitlist):,}")
col3.metric("Total (incl. Waitlist)", f"{int(total_including_waitlist):,}")
col4.metric("Utilization %", f"{utilization_pct:.1f}%")

st.divider()

# ---------- Data Table ----------
st.subheader(f"Filtered Results ({len(filtered_df)} rows)")
st.dataframe(filtered_df, use_container_width=True)
