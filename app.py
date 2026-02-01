import streamlit as st
import pandas as pd
from datetime import datetime, time
import os

st.set_page_config(page_title="Life Controller", layout="centered")

HABITS_FILE = "habits.csv"
HISTORY_FILE = "history.csv"
CONFIG_FILE = "config.csv"

DEFAULT_HABITS = [
    "Focused Work",
    "Learn Something",
    "Move Body",
    "Sleep On Time"
]

COLLEGE_SCHEDULE = {
    "COLLEGE DAY": [
        (time(6, 15), time(6, 25), "Wake up", None),
        (time(6, 25), time(6, 45), "Learn Something", "Learn Something"),
        (time(6, 45), time(7, 40), "Morning prep", None),
        (time(7, 40), time(9, 0), "Commute", None),
        (time(9, 0), time(16, 0), "College", None),
        (time(16, 0), time(18, 0), "Commute / Break", None),
        (time(18, 0), time(19, 0), "Focused Work", "Focused Work"),
        (time(19, 0), time(19, 20), "Move Body", "Move Body"),
        (time(19, 20), time(21, 45), "Free time", None),
        (time(21, 45), time(22, 15), "Sleep prep", "Sleep On Time"),
        (time(22, 15), time(23, 59), "Sleep", None)
    ],
    "HOLIDAY": [
        (time(6, 30), time(7, 0), "Learn Something", "Learn Something"),
        (time(7, 0), time(9, 0), "Morning routine", None),
        (time(9, 0), time(10, 30), "Focused Work Block 1", "Focused Work"),
        (time(10, 30), time(11, 0), "Break", None),
        (time(11, 0), time(12, 30), "Focused Work Block 2", "Focused Work"),
        (time(12, 30), time(16, 0), "Free time", None),
        (time(16, 0), time(17, 0), "Move Body", "Move Body"),
        (time(17, 0), time(22, 30), "Free time", None),
        (time(22, 30), time(23, 59), "Sleep", "Sleep On Time")
    ]
}

def init_files():
    if not os.path.exists(HABITS_FILE):
        pd.DataFrame({"habit": DEFAULT_HABITS}).to_csv(HABITS_FILE, index=False)
    if not os.path.exists(HISTORY_FILE):
        pd.DataFrame(columns=["date", "habit", "completed"]).to_csv(HISTORY_FILE, index=False)
    if not os.path.exists(CONFIG_FILE):
        pd.DataFrame({"key": ["day_type"], "value": ["COLLEGE DAY"]}).to_csv(CONFIG_FILE, index=False)

def load_habits():
    return pd.read_csv(HABITS_FILE)

def load_history():
    return pd.read_csv(HISTORY_FILE)

def load_config():
    return pd.read_csv(CONFIG_FILE)

def save_config(key, value):
    df = load_config()
    df.loc[df['key'] == key, 'value'] = value
    df.to_csv(CONFIG_FILE, index=False)

def save_completion(date, habit, completed):
    df = load_history()
    df = df[~((df['date'] == date) & (df['habit'] == habit))]
    new_entry = pd.DataFrame({"date": [date], "habit": [habit], "completed": [completed]})
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(HISTORY_FILE, index=False)

def get_current_action(day_type, current_time):
    schedule = COLLEGE_SCHEDULE.get(day_type, COLLEGE_SCHEDULE["COLLEGE DAY"])
    for start, end, action, habit in schedule:
        if start <= current_time < end:
            duration = (datetime.combine(datetime.today(), end) - datetime.combine(datetime.today(), current_time)).seconds // 60
            return action, habit, duration
    return "Sleep", None, 0

def check_day_status(date_str, day_type):
    df = load_history()
    today_data = df[df['date'] == date_str]
    
    if day_type == "COLLEGE DAY":
        focused_work = today_data[today_data['habit'] == 'Focused Work']
        if focused_work.empty or not focused_work.iloc[0]['completed']:
            return "FAILED"
    
    if today_data.empty:
        return "INCOMPLETE"
    
    total = len(today_data)
    completed = today_data['completed'].sum()
    
    if completed == total:
        return "SUCCESS"
    return "INCOMPLETE"

init_files()

now = datetime.now()
current_time = now.time()
today_str = now.strftime("%Y-%m-%d")

config_df = load_config()
day_type = config_df[config_df['key'] == 'day_type']['value'].iloc[0]

st.title("⚡ Life Controller")

col1, col2 = st.columns(2)
with col1:
    if st.button("COLLEGE DAY", use_container_width=True, type="primary" if day_type == "COLLEGE DAY" else "secondary"):
        save_config("day_type", "COLLEGE DAY")
        st.rerun()
with col2:
    if st.button("HOLIDAY", use_container_width=True, type="primary" if day_type == "HOLIDAY" else "secondary"):
        save_config("day_type", "HOLIDAY")
        st.rerun()

st.divider()

action, habit_name, duration = get_current_action(day_type, current_time)

st.subheader("⏰ NOW")
st.write(f"**Time:** {now.strftime('%I:%M %p')}")
st.write(f"**Day Type:** {day_type}")
st.write(f"**Action:** {action}")
if duration > 0:
    st.write(f"**Duration:** {duration} min")
if habit_name:
    st.write(f"**Habit:** {habit_name}")

st.divider()

day_status = check_day_status(today_str, day_type)
if day_status == "FAILED":
    st.error("❌ DAY FAILED — Focused Work not completed")
elif day_status == "SUCCESS":
    st.success("✅ DAY SUCCESS")
else:
    st.info("⏳ DAY INCOMPLETE")

st.divider()

st.subheader("📋 Today's Habits")

habits_df = load_habits()
history_df = load_history()
today_history = history_df[history_df['date'] == today_str]

completed_count = 0
total_habits = len(habits_df)

for idx, row in habits_df.iterrows():
    habit = row['habit']
    
    is_completed = False
    if not today_history.empty:
        habit_row = today_history[today_history['habit'] == habit]
        if not habit_row.empty:
            is_completed = bool(habit_row.iloc[0]['completed'])
    
    checked = st.checkbox(habit, value=is_completed, key=f"habit_{idx}")
    
    if checked != is_completed:
        save_completion(today_str, habit, checked)
        st.rerun()
    
    if checked:
        completed_count += 1

st.divider()

progress = completed_count / total_habits if total_habits > 0 else 0
st.write(f"**Progress:** {completed_count}/{total_habits}")
st.progress(progress)

if not history_df.empty and len(history_df) > 0:
    st.divider()
    st.subheader("📈 Completion Rate")
    
    daily = history_df.groupby('date').agg(
        completed_count=('completed', 'sum'),
        total_count=('completed', 'count')
    ).reset_index()
    
    daily['completion_rate'] = (daily['completed_count'] / daily['total_count'] * 100).round(1)
    daily['date'] = pd.to_datetime(daily['date'])
    daily = daily.sort_values('date')
    
    st.line_chart(daily.set_index('date')['completion_rate'], use_container_width=True)
