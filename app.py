import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Habit Tracker", layout="centered")

HABITS_FILE = "habits.csv"
HISTORY_FILE = "history.csv"

DEFAULT_HABITS = [
    "Deep Work",
    "Exercise",
    "Learning",
    "Sleep before 12"
]

def init_files():
    if not os.path.exists(HABITS_FILE):
        pd.DataFrame({"habit": DEFAULT_HABITS}).to_csv(HABITS_FILE, index=False)
    if not os.path.exists(HISTORY_FILE):
        pd.DataFrame(columns=["date", "habit", "completed"]).to_csv(HISTORY_FILE, index=False)

def load_habits():
    return pd.read_csv(HABITS_FILE)

def load_history():
    return pd.read_csv(HISTORY_FILE)

def save_habit(habit_name):
    df = load_habits()
    new_habit = pd.DataFrame({"habit": [habit_name]})
    df = pd.concat([df, new_habit], ignore_index=True)
    df.to_csv(HABITS_FILE, index=False)

def delete_habit(habit_name):
    df = load_habits()
    df = df[df["habit"] != habit_name]
    df.to_csv(HABITS_FILE, index=False)

def save_completion(date, habit, completed):
    df = load_history()
    df = df[~((df['date'] == date) & (df['habit'] == habit))]
    new_entry = pd.DataFrame({"date": [date], "habit": [habit], "completed": [completed]})
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(HISTORY_FILE, index=False)

init_files()

today = datetime.now().date()
today_str = today.strftime("%Y-%m-%d")

st.title("🎯 Habit Tracker")
st.subheader(f"📅 {today.strftime('%B %d, %Y')}")

with st.expander("➕ Add New Habit"):
    new_habit = st.text_input("Habit name", key="new_habit_input")
    if st.button("Add Habit", use_container_width=True):
        if new_habit.strip():
            save_habit(new_habit.strip())
            st.success(f"Added: {new_habit}")
            st.rerun()

st.divider()

habits_df = load_habits()
history_df = load_history()

if habits_df.empty:
    st.info("👆 Add your first habit above!")
else:
    today_history = history_df[history_df['date'] == today_str]
    
    st.subheader("Today's Habits")
    
    completed_count = 0
    total_habits = len(habits_df)
    
    for idx, row in habits_df.iterrows():
        habit_name = row['habit']
        
        is_completed = False
        if not today_history.empty:
            habit_row = today_history[today_history['habit'] == habit_name]
            if not habit_row.empty:
                is_completed = bool(habit_row.iloc[0]['completed'])
        
        col1, col2 = st.columns([0.85, 0.15])
        
        with col1:
            checked = st.checkbox(habit_name, value=is_completed, key=f"habit_{idx}")
        
        with col2:
            if st.button("🗑️", key=f"del_{idx}"):
                delete_habit(habit_name)
                st.rerun()
        
        if checked != is_completed:
            save_completion(today_str, habit_name, checked)
        
        if checked:
            completed_count += 1
    
    st.divider()
    
    progress = completed_count / total_habits if total_habits > 0 else 0
    st.subheader(f"Today's Progress: {completed_count}/{total_habits}")
    st.progress(progress)
    st.write(f"{int(progress * 100)}% Complete")
    
    if not history_df.empty and len(history_df) > 0:
        st.divider()
        st.subheader("📈 Completion Over Time")
        
        daily = history_df.groupby('date').agg(
            completed_count=('completed', 'sum'),
            total_count=('completed', 'count')
        ).reset_index()
        
        daily['completion_rate'] = (daily['completed_count'] / daily['total_count'] * 100).round(1)
        daily['date'] = pd.to_datetime(daily['date'])
        daily = daily.sort_values('date')
        
        st.line_chart(daily.set_index('date')['completion_rate'], use_container_width=True)
