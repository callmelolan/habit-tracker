import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="Life Controller", layout="centered", initial_sidebar_state="collapsed")

IST = ZoneInfo("Asia/Kolkata")
HISTORY_FILE = "history.csv"
CONFIG_FILE = "config.csv"

CORE_HABITS = ["Focused Work", "Learn Something", "Move Body", "Sleep On Time"]

COLLEGE_SCHEDULE = [
    (time(6, 15), time(6, 25), "Wake", None),
    (time(6, 25), time(6, 45), "Learn Something", "Learn Something"),
    (time(6, 45), time(7, 40), "Morning prep", None),
    (time(7, 40), time(9, 0), "Commute", None),
    (time(9, 0), time(16, 0), "College", None),
    (time(16, 0), time(18, 0), "Commute / Break", None),
    (time(18, 0), time(19, 0), "Focused Work", "Focused Work"),
    (time(19, 0), time(19, 20), "Move Body", "Move Body"),
    (time(19, 20), time(20, 0), "Free time", None),
    (time(20, 0), time(21, 0), "Gaming", None),
    (time(21, 0), time(21, 45), "Free time", None),
    (time(21, 45), time(22, 15), "Sleep prep", "Sleep On Time"),
    (time(22, 15), time(23, 59), "Sleep", None)
]

HOLIDAY_SCHEDULE = [
    (time(6, 30), time(7, 0), "Learn Something", "Learn Something"),
    (time(7, 0), time(9, 0), "Morning routine", None),
    (time(9, 0), time(10, 30), "Focused Work Block 1", "Focused Work"),
    (time(10, 30), time(11, 0), "Break", None),
    (time(11, 0), time(12, 30), "Focused Work Block 2", "Focused Work"),
    (time(12, 30), time(16, 0), "Free time", None),
    (time(16, 0), time(17, 0), "Move Body", "Move Body"),
    (time(17, 0), time(18, 0), "Free time", None),
    (time(18, 0), time(20, 0), "Gaming", None),
    (time(20, 0), time(22, 30), "Free time", None),
    (time(22, 30), time(23, 59), "Sleep", "Sleep On Time")
]

def get_now_ist():
    return datetime.now(IST)

def init_files():
    if not os.path.exists(HISTORY_FILE):
        pd.DataFrame(columns=["date", "habit", "completed", "day_type", "miss_reason"]).to_csv(HISTORY_FILE, index=False)
    if not os.path.exists(CONFIG_FILE):
        pd.DataFrame({"key": ["day_type"], "value": ["College Day"]}).to_csv(CONFIG_FILE, index=False)

def load_history():
    return pd.read_csv(HISTORY_FILE)

def load_config():
    return pd.read_csv(CONFIG_FILE)

def save_config(key, value):
    df = load_config()
    if key in df['key'].values:
        df.loc[df['key'] == key, 'value'] = value
    else:
        new_row = pd.DataFrame({"key": [key], "value": [value]})
        df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(CONFIG_FILE, index=False)

def save_completion(date, habit, completed, day_type, miss_reason=""):
    df = load_history()
    df = df[~((df['date'] == date) & (df['habit'] == habit))]
    new_entry = pd.DataFrame({
        "date": [date],
        "habit": [habit],
        "completed": [completed],
        "day_type": [day_type],
        "miss_reason": [miss_reason]
    })
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(HISTORY_FILE, index=False)

def get_current_action(day_type, current_time):
    schedule = COLLEGE_SCHEDULE if day_type == "College Day" else HOLIDAY_SCHEDULE
    for start, end, action, habit in schedule:
        if start <= current_time < end:
            duration = (datetime.combine(datetime.today(), end) - datetime.combine(datetime.today(), current_time)).seconds // 60
            return action, habit, duration
    return "Sleep", None, 0

def check_day_status(date_str, day_type):
    df = load_history()
    today_data = df[df['date'] == date_str]
    
    if day_type == "College Day":
        focused_work = today_data[today_data['habit'] == 'Focused Work']
        if focused_work.empty or not focused_work.iloc[0]['completed']:
            return "FAILED"
    
    if today_data.empty:
        return "INCOMPLETE"
    
    total = len(CORE_HABITS)
    completed = today_data['completed'].sum()
    
    if completed == total:
        return "SUCCESS"
    return "INCOMPLETE"

def check_gaming_status(date_str, day_type):
    df = load_history()
    today_data = df[df['date'] == date_str]
    
    if day_type == "College Day":
        focused_work = today_data[today_data['habit'] == 'Focused Work']
        if not focused_work.empty and focused_work.iloc[0]['completed']:
            return "ALLOWED"
        return "LOCKED"
    else:
        focused_work = today_data[today_data['habit'] == 'Focused Work']
        if not focused_work.empty and focused_work['completed'].any():
            return "ALLOWED"
        return "LOCKED"

def get_weekly_analytics():
    df = load_history()
    if df.empty:
        return None
    
    now_ist = get_now_ist()
    last_7_days = [(now_ist - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    
    df_week = df[df['date'].isin(last_7_days)]
    
    if df_week.empty:
        return None
    
    summary = df_week.groupby('habit').agg(
        total=('completed', 'count'),
        completed=('completed', 'sum')
    ).reset_index()
    
    summary['completion_pct'] = (summary['completed'] / summary['total'] * 100).round(1)
    
    return summary

init_files()

now_ist = get_now_ist()
current_time = now_ist.time()
today_str = now_ist.strftime("%Y-%m-%d")

config_df = load_config()
day_type_row = config_df[config_df['key'] == 'day_type']
day_type = day_type_row['value'].iloc[0] if not day_type_row.empty else "College Day"

st.title("⚡ Life Controller")

with st.expander("📘 What Counts as What"):
    st.markdown("""
    **Focused Work — COUNTS AS:**
    - muLearn tasks
    - NPTEL assignments
    - Python practice
    - App development (Habit Tracker / Jarvis)
    - Debugging code
    - Writing logic
    - CLI / automation work
    
    **❌ Does NOT Count:**
    - Watching videos
    - Reading notes
    - College classes
    - Multitasking
    - Casual browsing
    
    ---
    
    **Learn Something — COUNTS AS:**
    - muLearn videos
    - NPTEL videos
    - Reading PDFs / notes
    - Concept revision
    
    **❌ Does NOT Count:**
    - Coding
    - Assignments
    - Projects
    
    ---
    
    **Move Body — COUNTS AS:**
    - Walking
    - Stretching
    - Light workout
    - Mobility drills
    
    **❌ Does NOT Count:**
    - Sitting
    - Gaming
    - Scrolling
    
    ---
    
    **Sleep On Time — COUNTS AS:**
    - Phone away by 9:45 PM
    - In bed by 10:15 PM
    
    **❌ Does NOT Count:**
    - "Almost slept"
    - Late scrolling
    - Late gaming
    """)

st.divider()

st.subheader("📅 Day Type")
col1, col2 = st.columns(2)
with col1:
    if st.button("College Day", use_container_width=True, type="primary" if day_type == "College Day" else "secondary"):
        save_config("day_type", "College Day")
        st.rerun()
with col2:
    if st.button("Holiday", use_container_width=True, type="primary" if day_type == "Holiday" else "secondary"):
        save_config("day_type", "Holiday")
        st.rerun()

st.divider()

st.subheader("⏰ Current Time (IST)")
st.write(f"**{now_ist.strftime('%I:%M %p')} — {now_ist.strftime('%A, %B %d, %Y')}**")

st.divider()

action, habit_name, duration = get_current_action(day_type, current_time)

st.subheader("🎯 What Should I Be Doing Now?")
st.write(f"**Action:** {action}")
if duration > 0:
    st.write(f"**Time Remaining:** {duration} min")
if habit_name:
    st.write(f"**Habit:** {habit_name}")

gaming_status = check_gaming_status(today_str, day_type)
if action == "Gaming":
    if gaming_status == "ALLOWED":
        st.success("🎮 Gaming ALLOWED")
    else:
        st.error("🔒 Gaming LOCKED — Complete Focused Work first")

st.divider()

st.subheader("✅ Today's Habits")

history_df = load_history()
today_history = history_df[history_df['date'] == today_str]

completed_count = 0

for habit in CORE_HABITS:
    is_completed = False
    miss_reason = ""
    
    if not today_history.empty:
        habit_row = today_history[today_history['habit'] == habit]
        if not habit_row.empty:
            is_completed = bool(habit_row.iloc[0]['completed'])
            miss_reason = habit_row.iloc[0].get('miss_reason', "") if not is_completed else ""
    
    col1, col2 = st.columns([0.7, 0.3])
    
    with col1:
        checked = st.checkbox(habit, value=is_completed, key=f"habit_{habit}")
    
    with col2:
        if not is_completed and not checked:
            reason = st.selectbox(
                "Why?",
                ["", "Time", "Energy", "Distraction"],
                key=f"reason_{habit}",
                label_visibility="collapsed"
            )
            if reason:
                miss_reason = reason
    
    if checked != is_completed:
        save_completion(today_str, habit, checked, day_type, miss_reason if not checked else "")
        st.rerun()
    
    if checked:
        completed_count += 1

st.divider()

day_status = check_day_status(today_str, day_type)
if day_status == "FAILED":
    st.error("❌ DAY FAILED — Focused Work not completed")
elif day_status == "SUCCESS":
    st.success("✅ DAY SUCCESS")
else:
    st.warning("⏳ DAY INCOMPLETE")

progress = completed_count / len(CORE_HABITS)
st.write(f"**Progress:** {completed_count}/{len(CORE_HABITS)} ({int(progress * 100)}%)")
st.progress(progress)

st.divider()

st.subheader("📊 Weekly Analytics")

weekly_data = get_weekly_analytics()

if weekly_data is not None and not weekly_data.empty:
    st.dataframe(weekly_data, use_container_width=True, hide_index=True)
    
    chart_data = weekly_data.set_index('habit')['completion_pct']
    st.bar_chart(chart_data, use_container_width=True)
else:
    st.info("No data yet. Complete habits to see analytics.")
