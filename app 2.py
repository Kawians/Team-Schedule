import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# Define shift structure & break rules
shifts = {
    "Toronto (8 AM - 4 PM)": {"default_start": 8, "default_end": 16, "adjustable_range": (8, 18), "break_slots": [(9.5, 9.75), (13.5, 13.75)], "lunch_range": (11.5, 13)},
    "Toronto (10 AM - 6 PM)": {"default_start": 10, "default_end": 18, "adjustable_range": (8, 18), "break_slots": [(11, 11.25), (15, 15.25)], "lunch_range": (12.5, 14)},
    "Bogotá (7 AM - 4:30 PM)": {"default_start": 7, "default_end": 16.5, "adjustable_range": (7, 18), "break_slots": [(9, 9.5)], "lunch_range": (11.5, 13.5)},
    "Bogotá (8:30 AM - 6 PM)": {"default_start": 8.5, "default_end": 18, "adjustable_range": (7, 18), "break_slots": [(10, 10.5)], "lunch_range": (12, 14)}
}

# Function to format float times into HH:MM format
def format_time(hour):
    hour_int = int(hour)
    minute = int((hour - hour_int) * 60)
    return f"{hour_int:02d}:{minute:02d}"

# Upload Employee List
st.sidebar.header("Step 1: Upload Employee List (Excel)")
uploaded_file = st.sidebar.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file:
    df_employees = pd.read_excel(uploaded_file)
    if "Employee" not in df_employees.columns:
        st.sidebar.error("Excel file must contain an 'Employee' column!")
        df_employees = None
else:
    df_employees = None

# Assign employees to shifts while preventing duplicates
assigned_employees = set()
employee_shifts = {}

if df_employees is not None:
    st.sidebar.header("Step 2: Assign Employees to Shifts")
    available_employees = df_employees["Employee"].tolist()

    for shift in shifts.keys():
        remaining_employees = [e for e in available_employees if e not in assigned_employees]
        selected_employees = st.sidebar.multiselect(
            f"{shift} Employees", remaining_employees, key=f"shift_{shift}"
        )
        employee_shifts[shift] = selected_employees
        assigned_employees.update(selected_employees)

# Generate Schedule Button
if st.sidebar.button("Generate Schedule") and df_employees is not None:
    schedule_data = []
    gantt_data = []
    for shift, assigned_employees in employee_shifts.items():
        shift_info = shifts[shift]
        lunch_start, lunch_end = shift_info["lunch_range"]
        break_slots = shift_info["break_slots"]

        # Stagger breaks & lunch assignment
        break_intervals = []
        for slot_start, slot_end in break_slots:
            break_times = np.linspace(slot_start, slot_end, len(assigned_employees))
            break_intervals.append([round(b, 2) for b in break_times])

        lunch_intervals = np.linspace(lunch_start, lunch_end, len(assigned_employees))
        lunch_intervals = [round(l, 1) for l in lunch_intervals]

        for i, employee in enumerate(assigned_employees):
            assigned_breaks = [f"{format_time(break_intervals[j][i])} - {format_time(break_intervals[j][i] + 0.5)}" for j in range(len(break_slots))]
            assigned_lunch = format_time(lunch_intervals[i])
            schedule_data.append([shift, employee, format_time(shift_info['default_start']), format_time(shift_info['default_end']), ", ".join(assigned_breaks), assigned_lunch])

            gantt_data.append({"Task": employee, "Start": format_time(shift_info['default_start']), "Finish": format_time(shift_info['default_end']), "Category": shift})
            for break_time in assigned_breaks:
                start_break, end_break = break_time.split(" - ")
                gantt_data.append({"Task": employee, "Start": start_break, "Finish": end_break, "Category": "Break"})
            gantt_data.append({"Task": employee, "Start": assigned_lunch, "Finish": format_time(float(assigned_lunch.split(":" )[0]) + (0.5 if "Toronto" in shift else 1.0)), "Category": "Lunch"})

    df_schedule = pd.DataFrame(schedule_data, columns=["Shift", "Employee", "Start Time", "End Time", "Breaks", "Lunch"])
    df_gantt = pd.DataFrame(gantt_data)
    st.session_state.df_schedule = df_schedule.copy()

# If a schedule exists, show it with live adjustments
if "df_schedule" in st.session_state:
    st.subheader("Step 2: Adjust Shifts, Breaks & Lunch Live")
    df_schedule = st.session_state.df_schedule
    st.write(df_schedule)

    fig = px.timeline(df_gantt, x_start="Start", x_end="Finish", y="Task", color="Category", title="Weekly Shift Plan with Breaks & Lunch")
    fig.update_layout(height=800, xaxis_title="Time", yaxis_title="Employees", showlegend=True)
    st.subheader("Detailed Weekly Shift Plan")
    st.plotly_chart(fig, use_container_width=True)
