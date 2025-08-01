import streamlit as st
import pandas as pd
import json
from datetime import date, datetime
import os
# Removed streamlit_calendar (replaced with built-in calendar layout)

# --- CONFIG ---
st.set_page_config(page_title="🎯 Daily Job App Tracker", layout="wide")
TRACKER_CSV = "job_applications.csv"
SUMMARY_JSON = "daily_summary.json"
EVENTS_JSON = "calendar_events.json"
UPLOAD_DIR = "uploaded_resumes"
LOGS_DIR = "logs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# --- USER AUTH ---
USERS = {
    "aishwarya": {"password": "applydaily", "role": "user"},
    "Prasad": {"password": "seetracker", "role": "viewer"},
}
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None

def login():
    with st.sidebar:
        st.title("🔐 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = USERS.get(username)
            if user and user["password"] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.role = user["role"]
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

def logout():
    with st.sidebar:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()

if not st.session_state.authenticated:
    login()
    st.stop()
else:
    logout()

# --- Load Data ---
if os.path.exists(TRACKER_CSV):
    df = pd.read_csv(TRACKER_CSV)
else:
    df = pd.DataFrame(columns=["Date", "Platform", "Company", "Job Link", "Status", "Notes", "Resume"])

if os.path.exists(SUMMARY_JSON):
    with open(SUMMARY_JSON, 'r') as f:
        summary_data = json.load(f)
else:
    summary_data = {}

if os.path.exists(EVENTS_JSON):
    with open(EVENTS_JSON, 'r') as f:
        calendar_events = json.load(f)
else:
    calendar_events = []

# --- DAILY SUMMARY + CHECKLIST ---
today = date.today().isoformat()
if today not in summary_data:
    summary_data[today] = {
        "counts": {},
        "checklist": {
            "resume_custom": False,
            "cover_custom": False,
            "networking_1": False,
            "networking_2": False,
            "tracker_update": False,
            "followup_marked": False
        }
    }

# --- UI HEADER ---
st.title("🎯 Daily Job Application Tracker")
st.markdown("Keep track of your job hunt visually, securely, and in real time!")

# --- APPLICATION COUNTS ---
st.markdown("---")
st.header("📌 Daily Applications Summary")
platforms = summary_data[today]["counts"]

col1, col2, col3 = st.columns(3)
with col1:
    platforms["LinkedIn"] = st.slider("LinkedIn", 0, 20, platforms.get("LinkedIn", 0))
    platforms["Handshake"] = st.slider("Handshake", 0, 10, platforms.get("Handshake", 0))
with col2:
    platforms["Indeed"] = st.slider("Indeed", 0, 20, platforms.get("Indeed", 0))
    platforms["Wellfound / ZipRecruiter"] = st.slider("Wellfound / ZipRecruiter", 0, 10, platforms.get("Wellfound / ZipRecruiter", 0))
with col3:
    platforms["Company Sites"] = st.slider("Company Sites", 0, 10, platforms.get("Company Sites", 0))
    other_platform = st.text_input("Other Platform Name")
    other_count = st.number_input("Count (Other Platform)", min_value=0, step=1)

if other_platform:
    platforms[other_platform] = other_count

st.markdown(f"#### 🎯 Total Applications Today: **{sum(platforms.values())}**")

# --- CHECKLIST ---
st.markdown("---")
st.header("✅ Daily Checklist")
with st.expander("Show/Hide Checklist"):
    for key in summary_data[today]["checklist"]:
        summary_data[today]["checklist"][key] = st.checkbox(key.replace("_", " ").capitalize(), value=summary_data[today]["checklist"][key], key=key)

# --- CALENDAR + REMINDERS ---
st.sidebar.header("📅 Schedule a Reminder")
with st.sidebar.form("add_event", clear_on_submit=True):
    title = st.text_input("Event Title")
    event_date = st.date_input("Select Date")
    time_str = st.time_input("Reminder Time")
    note = st.text_area("Notes")
    add = st.form_submit_button("➕ Add Event")

    if add:
        event = {
            "title": title,
            "start": f"{event_date}T{time_str}",
            "end": f"{event_date}T{time_str}",
            "note": note
        }
        calendar_events.append(event)
        with open(EVENTS_JSON, 'w') as f:
            json.dump(calendar_events, f)
        st.sidebar.success("📌 Event added!")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🗓️ Upcoming Events")
for idx, event in enumerate(sorted(calendar_events, key=lambda e: e['start'])):
    label = f"❌ {event['title']} on {event['start'][:10]}"
    if st.sidebar.button(label, key=f"delete_event_{idx}"):
        calendar_events.remove(event)
        with open(EVENTS_JSON, 'w') as f:
            json.dump(calendar_events, f)
        st.sidebar.success("🗑️ Event deleted.")
        st.rerun()

# --- JOB LOGGING FORM (only for 'user' role') ---
st.markdown("---")
st.header("🗂 Log a Job Application")

if st.session_state.role != "viewer":
    with st.form("log_job_form"):
        cols = st.columns(2)
        platform = cols[0].selectbox("Platform", list(platforms.keys()))
        company = cols[1].text_input("Company Name")
        link = st.text_input("Job Link")
        status = st.selectbox("Status", ["Applied", "Interview", "Rejected", "Offer", "Followed Up"])
        notes = st.text_area("Notes")
        resume_file = st.file_uploader("Upload Resume Used (PDF)", type=["pdf"])
        submit = st.form_submit_button("➕ Log Application")

        if submit:
            resume_path = ""
            if resume_file:
                safe_name = f"{today}_{company.replace(' ', '_')}_{resume_file.name}"
                resume_path = os.path.join(UPLOAD_DIR, safe_name)
                with open(resume_path, "wb") as f:
                    f.write(resume_file.read())

            new_entry = {
                "Date": today,
                "Platform": platform,
                "Company": company,
                "Job Link": link,
                "Status": status,
                "Notes": notes,
                "Resume": resume_path
            }
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            # Save to master file
            df.to_csv(TRACKER_CSV, index=False)

            # Save to a dated file as well
            daily_filename = f"logs/{today}_applications.csv"
            os.makedirs("logs", exist_ok=True)
            df[df["Date"] == today].to_csv(daily_filename, index=False)


            with open(SUMMARY_JSON, 'w') as f:
                json.dump(summary_data, f)

            st.success(f"✅ Application to {company} logged!")
            st.rerun()
else:
    st.info("🔒 Viewer Mode: You can view applications but not add new entries.")

# --- VIEW + MANAGE APPLICATIONS ---
st.markdown("---")
st.header("📄 Application History")

if not df.empty:
    for i, row in df[::-1].reset_index(drop=True).iterrows():
        with st.expander(f"{row['Company']} ({row['Platform']}) - {row['Status']}"):
            st.markdown(f"**Date:** {row['Date']}")
            st.markdown(f"🔗 [Job Link]({row['Job Link']})")
            st.markdown(f"📝 Notes: {row['Notes']}")
            if row['Resume']:
                st.markdown(f"📎 [Download Resume]({row['Resume']})")

            col1, col2 = st.columns(2)
            if col1.button("📝 Edit", key=f"edit_{i}"):
                st.session_state.edit_index = i
                st.rerun()
            if col2.button("❌ Delete", key=f"delete_{i}"):
                df.drop(df.index[::-1][i], inplace=True)
                df.to_csv(TRACKER_CSV, index=False)
                st.success("Entry deleted.")
                st.rerun()

# --- EDIT APPLICATION MODE ---
if "edit_index" in st.session_state:
    idx = st.session_state.edit_index
    row = df.iloc[::-1].reset_index(drop=True).iloc[idx]
    st.markdown("---")
    st.header("✏️ Edit Application")
    with st.form("edit_form"):
        cols = st.columns(2)
        platform = cols[0].selectbox("Platform", list(platforms.keys()), index=list(platforms.keys()).index(row["Platform"]))
        company = cols[1].text_input("Company Name", value=row["Company"])
        link = st.text_input("Job Link", value=row["Job Link"])
        status = st.selectbox("Status", ["Applied", "Interview", "Rejected", "Offer", "Followed Up"], index=["Applied", "Interview", "Rejected", "Offer", "Followed Up"].index(row["Status"]))
        notes = st.text_area("Notes", value=row["Notes"])
        submit = st.form_submit_button("💾 Save Changes")

        if submit:
            real_idx = df.index[::-1][idx]
            df.at[real_idx, "Platform"] = platform
            df.at[real_idx, "Company"] = company
            df.at[real_idx, "Job Link"] = link
            df.at[real_idx, "Status"] = status
            df.at[real_idx, "Notes"] = notes
            df.to_csv(TRACKER_CSV, index=False)
            del st.session_state.edit_index
            st.success("Application updated.")
            st.rerun()
st.markdown("---")
st.header("📅 View Applications by Date")

all_logs = sorted([f for f in os.listdir(LOGS_DIR) if f.endswith(".csv")])
dates_available = [f.split("_applications.csv")[0] for f in all_logs]

if dates_available:
    selected_date = st.selectbox("Select a date to view:", dates_available)

    selected_path = os.path.join("logs", f"{selected_date}_applications.csv")
    if os.path.exists(selected_path):
        day_df = pd.read_csv(selected_path)
        st.subheader(f"📄 Applications on {selected_date}")
        for i, row in day_df[::-1].reset_index(drop=True).iterrows():
            with st.expander(f"{row['Company']} ({row['Platform']}) - {row['Status']}"):
                st.markdown(f"**Date:** {row['Date']}")
                st.markdown(f"🔗 [Job Link]({row['Job Link']})")
                st.markdown(f"📝 Notes: {row['Notes']}")
                if row['Resume']:
                    st.markdown(f"📎 [Download Resume]({row['Resume']})")
else:
    st.info("No historical data saved yet.")

# --- EXPORT ---
if st.button("💾 Export All to CSV"):
    df.to_csv(TRACKER_CSV, index=False)
    with open(SUMMARY_JSON, 'w') as f:
        json.dump(summary_data, f)
    st.success("📁 Tracker saved!")

st.markdown("---")
st.caption("Developed by Aishwarya Rao — with resume upload, daily logs, checklist, calendar and viewer mode for Dad 🚀")
