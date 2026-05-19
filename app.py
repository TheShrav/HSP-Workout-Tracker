import streamlit as st
import pandas as pd
import datetime
import requests
import base64
import json

# --- GITHUB STORAGE CONFIGURATION ---
# These will be securely stored in Streamlit Cloud Secrets, NOT hardcoded!
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN")
REPO_NAME = st.secrets.get("REPO_NAME")      # Format: "your-username/your-repo-name"
FILE_PATH = "workout_logs.csv"                # The file inside your repo
BRANCH = "main"

HSP_PROGRAM = {
    "Day 1: Heavy (H)": {
        "description": "Low reps, high intensity. Rest: 2-3m Compounds, 90s Isolations. Target: RPE 8-9.",
        "exercises": ["Barbell Squat (4 x 4-6)", "Bench Press (4 x 4-6)", "Barbell Row (4 x 4-6)", "Lat Machine Row (3 x 4-6)", "Romanian Deadlift (3 x 4-6)", "Shoulder Press (3 x 4-6)", "Superset: Tricep Pushdown (2 x 6-8)", "Superset: Bicep Curl (2 x 6-8)"]
    },
    "Day 2: Stretch (S) - Week A": {
        "description": "Moderate reps, lengthened muscle position. Rest: 90s-2m Compounds, 60-90s Isolations.",
        "exercises": ["Hamstring Curl (3 x 8-10)", "Hack Squats (3 x 8-10)", "Incline Bench Press (3 x 8-10)", "Lat Pulldown / Pull Ups (3 x 8-10)", "Kelso Shrugs (3 x 8-10)", "Side Delt Lateral Raise (3 x 8-10)", "Rear Delt Fly (3 x 8-10)", "Overhead Tricep Extensions (3 x 8-10)", "Incline Bicep Curl (3 x 8-10)", "Hammer Curl (3 x 8-10)", "Calves (Machine/Leg Press) (3 x 8-12)"]
    },
    "Day 2: Stretch (S) - Week B": {
        "description": "Moderate reps, lengthened muscle position. Rest: 90s-2m Compounds, 60-90s Isolations.",
        "exercises": ["Hip Thrust (3 x 8-10)", "Leg Extension - Max Stretch (3 x 8-10)", "Incline Bench Press (3 x 8-10)", "Lat Pulldown / Pull Ups (3 x 8-10)", "Kelso Shrugs (3 x 8-10)", "Side Delt Lateral Raise (3 x 8-10)", "Rear Delt Fly (3 x 8-10)", "Overhead Tricep Extensions (3 x 8-10)", "Incline Bicep Curl (3 x 8-10)", "Hammer Curl (3 x 8-10)", "Calves (Machine/Leg Press) (3 x 8-12)"]
    },
    "Day 3: Pump (P)": {
        "description": "High reps, short rest (30-90s), metabolic stress. Supersets encouraged!",
        "exercises": ["Seated Hamstring Curl (3-4 x 12-15)", "Leg Extension (3-4 x 12-15)", "Chest Pec Dec / Cable Chest Fly (3-4 x 12-15)", "Cable Row - Traps/Rhomboids (3-4 x 12-15)", "Seated Cable Row - Lats (3-4 x 12-15)", "Front Delt Shoulder Press (3-4 x 12-30)", "Side Delt Lateral Raise (3-4 x 12-20)", "Rear Delt Fly (3-4 x 12-20)", "Tricep Pushdown Cable (3-4 x 12-20)", "Bicep Curl Cable / Incline Curl (3-4 x 12-20)", "Hip Abductor - Sus Machine (3-4 x 12-15)", "Calves (Machine/Leg Press) (3-4 x 8-12)"]
    },
    "Cardio & Small Muscle Groups": {
        "description": "Core, Forearms, Lower Back, Calves, Neck & Conditioning.",
        "exercises": ["Abs: Ab Crunch (3-4 x 12-20)", "Abs: Lower Ab Weighted Crunch (3-4 x 12-20)", "Abs: Cable Oblique Crunch (3-4 x 12-20)", "Abs: At-home Ab Circuit", "Forearms: Farmers Carry (3 x 40s)", "Forearms: Wrist Curl Cable (3-4 x 12-20)", "Forearms: Reverse Curl Cable (3-4 x 12-20)", "Lower Back Machine Extension (3-4 x 12-15)", "Calves (Machine/Leg Press) (3-5 x 8-12)", "Neck Curls", "Cardio: Steady State", "Cardio: HIIT", "Cardio: Sport", "Cardio: Active Recovery Walk"]
    }
}

# --- GITHUB API HELPERS ---
def get_github_file():
    """Fetches the CSV file from GitHub. If it doesn't exist, returns empty DataFrame and None sha."""
    if not GITHUB_TOKEN or not REPO_NAME:
        return pd.DataFrame(columns=["Date", "Routine", "Exercise", "Weight/Intensity", "Sets", "Reps", "Notes"]), None
    
    url = f"https://api.github.com/v1/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    
    if res.status_code == 200:
        file_data = res.json()
        csv_content = base64.b64decode(file_data["content"]).decode("utf-8")
        from io import StringIO
        df = pd.read_csv(StringIO(csv_content))
        return df, file_data["sha"]
    else:
        return pd.DataFrame(columns=["Date", "Routine", "Exercise", "Weight/Intensity", "Sets", "Reps", "Notes"]), None

def commit_to_github(df, sha=None):
    """Pushes data changes back to GitHub repository."""
    url = f"https://api.github.com/v1/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    csv_string = df.to_csv(index=False)
    content_bytes = base64.b64encode(csv_string.encode("utf-8")).decode("utf-8")
    
    data = {
        "message": "🏋️‍♂️ Update workout logs via HSP Web App",
        "content": content_bytes,
        "branch": BRANCH
    }
    if sha:
        data["sha"] = sha
        
    res = requests.put(url, headers=headers, data=json.dumps(data))
    return res.status_code in [200, 201]

# --- APP INTERFACE ---
st.set_page_config(page_title="HSP Cloud Tracker", page_icon="🏋️‍♂️", layout="wide")
st.title("🏋️‍♂️ HSP Cloud Workout Tracker")

# App Setup Guard checking for Cloud Configuration
if not GITHUB_TOKEN or not REPO_NAME:
    st.warning("⚠️ Cloud Storage configuration missing! Please add your GITHUB_TOKEN and REPO_NAME to Streamlit App Secrets.")
    st.stop()

# Fetch history live from GitHub
workout_df, file_sha = get_github_file()

tab1, tab2 = st.tabs(["📝 Log a Session", "📈 View & Export Progress"])

with tab1:
    st.subheader("Log Your Today's Training")
    st.info("💡 **HSP Rule:** Take a deload week every 4-6 weeks!")
    
    col1, col2 = st.columns(2)
    with col1:
        date_input = st.date_input("Training Date", datetime.date.today())
        routine_input = st.selectbox("Select Training Focus / Day", list(HSP_PROGRAM.keys()))
        st.caption(f"**Focus:** {HSP_PROGRAM[routine_input]['description']}")
        exercise_input = st.selectbox("Select Exercise", HSP_PROGRAM[routine_input]["exercises"])

    with col2:
        if any(keyword in exercise_input for keyword in ["Carry", "Steady", "HIIT", "Sport", "Walk"]):
            weight_input = st.text_input("Intensity Level / Speed", placeholder="e.g., 12% Incline, RPE 9")
            sets_input = st.number_input("Sets / Rounds", min_value=0, value=3)
            reps_input = st.text_input("Duration / Target", placeholder="e.g., 40 seconds, 45 minutes")
        else:
            weight_input = st.text_input("Weight Load Used", placeholder="e.g., 225 lbs, 60 kg")
            sets_input = st.number_input("Sets Completed", min_value=0, value=3)
            reps_input = st.text_input("Reps Completed per Set", placeholder="e.g., 5, 5, 4")

        notes_input = st.text_area("Performance Notes / RPE Feel")

    if st.button("💾 Log to Cloud Repo", type="primary"):
        new_row = {
            "Date": str(date_input), "Routine": routine_input, "Exercise": exercise_input,
            "Weight/Intensity": weight_input if weight_input else "N/A", "Sets": int(sets_input),
            "Reps": reps_input if reps_input else "N/A", "Notes": notes_input if notes_input else "None"
        }
        
        updated_df = pd.concat([workout_df, pd.DataFrame([new_row])], ignore_index=True)
        
        with st.spinner("Uploading logs securely to GitHub..."):
            success = commit_to_github(updated_df, file_sha)
            if success:
                st.success(f"Successfully recorded **{exercise_input}** to GitHub!")
                st.rerun()
            else:
                st.error("Failed to upload data. Double check your API token permissions.")

with tab2:
    st.subheader("📚 Saved Cloud Workout Logs")
    if not workout_df.empty:
        sorted_df = workout_df.sort_values(by="Date", ascending=False)
        st.dataframe(sorted_df, use_container_width=True)
    else:
        st.info("No cloud data logs found yet. Start tracking above!")
