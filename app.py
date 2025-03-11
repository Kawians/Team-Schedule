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

# Sidebar input
st.sidebar.header("Step 1: Enter Employees Per Shift")
employees_per_shift = {
    shift: st.sidebar.number_input(f"{shift}", min_value=0, step=1, value=3)
    for shift in shifts.keys()
}

# Function to format float times into HH:MM format
def format_time(hour):
    hour_int = int(hour)
    minute = int((hour - hour_int) * 60)
    return f"{hour_int:02d}:{minute:02d}"

# Button to generate schedule
if st.sidebar.button("Generate Schedule"):
    schedule_data = []
    for shift, num_employees in employees_per_shift.items():
        shift_info = shifts[shift]
        lunch_start, lunch_end = shift_info["lunch_range"]
        break_slots = shift_info["break_slots"]

        # Stagger breaks & lunch assignment
        break_intervals = []
        for slot_start, slot_end in break_slots:
            break_times = np.linspace(slot_start, slot_end, num_employees)
            break_intervals.append([round(b, 2) for b in break_times])

        lunch_intervals = np.linspace(lunch_start, lunch_end, num_employees)
        lunch_intervals = [round(l, 1) for l in lunch_intervals]

        for i in range(num_employees):
            assigned_breaks = [f"{format_time(break_intervals[j][i])} - {format_time(break_intervals[j][i] + 0.5)}" for j in range(len(break_slots))]
            assigned_lunch = format_time(lunch_intervals[i])
            schedule_data.append([shift, f"Employee {i+1}", format_time(shift_info["default_start"]), format_time(shift_info["default_end"]), ", ".join(assigned_breaks), assigned_lunch])

    df_schedule = pd.DataFrame(schedule_data, columns=["Shift", "Employee", "Start Time", "End Time", "Breaks", "Lunch"])
    st.session_state.df_schedule = df_schedule.copy()

# If a schedule exists, show it with live adjustments
if "df_schedule" in st.session_state:
    st.subheader("Step 2: Adjust Shifts, Breaks & Lunch Live")
    df_schedule = st.session_state.df_schedule

    for i in range(len(df_schedule)):
        shift_info = shifts[df_schedule.at[i, "Shift"]]
        min_start, max_end = shift_info["adjustable_range"]
        lunch_start, lunch_end = shift_info["lunch_range"]
        col1, col2, col3 = st.columns(3)

        with col1:
            df_schedule.at[i, "Start Time"] = format_time(st.slider(f"Start ({df_schedule.at[i, 'Employee']})", min_value=float(min_start), max_value=float(max_end - 1), step=0.5, value=float(df_schedule.at[i, "Start Time"].split(":" )[0])))

        with col2:
            df_schedule.at[i, "End Time"] = format_time(st.slider(f"End ({df_schedule.at[i, 'Employee']})", min_value=float(df_schedule.at[i, "Start Time"].split(":" )[0]) + 1, max_value=float(max_end), step=0.5, value=float(df_schedule.at[i, "End Time"].split(":" )[0])))

        with col3:
            lunch_time = float(df_schedule.at[i, "Lunch"].split(":")[0])
            lunch_duration = 0.5 if "Toronto" in df_schedule.at[i, "Shift"] else 1.0  # Toronto: 30 min, Bogotá: 1 hour
            new_lunch_time = st.slider(
                f"Lunch ({df_schedule.at[i, 'Employee']})",
                min_value=float(lunch_start), max_value=float(lunch_end - lunch_duration), step=0.5, value=lunch_time,
                key=f"lunch_slider_{i}"  # Unique key to avoid duplicate element ID error
            )
            df_schedule.at[i, "Lunch"] = f"{format_time(new_lunch_time)} - {format_time(new_lunch_time + lunch_duration)}"

    st.subheader("Final Schedule with Adjustments")
    st.write(df_schedule)

    
    # Create Gantt chart data with shift categories and distinct break & lunch times
    gantt_data = []
    for _, row in df_schedule.iterrows():
        # Add working shift as a main task
        gantt_data.append({
            "Task": f"{row['Employee']} ({row['Shift']})",  # Unique identifier per employee
            "Start": datetime.strptime(row["Start Time"], "%H:%M"),
            "Finish": datetime.strptime(row["End Time"], "%H:%M"),
            "Category": row["Shift"],  # Shift category (Selectable)
            "Type": f"Work - {row['Shift']}"  # Make each shift category selectable
        })

        # Add break times for this employee with higher z-index (layering priority)
        if row["Breaks"]:
            for break_time in row["Breaks"].split(", "):
                start_break, end_break = break_time.split(" - ")
                gantt_data.append({
                    "Task": f"{row['Employee']} ({row['Shift']})",
                    "Start": datetime.strptime(start_break, "%H:%M"),
                    "Finish": datetime.strptime(end_break, "%H:%M"),
                    "Category": "Break",  # Breaks are now selectable
                    "Type": "Break"
                })

        # Add lunch time for this employee, ensuring it's displayed correctly
        if " - " in row["Lunch"]:
            try:
                start_lunch, end_lunch = row["Lunch"].split(" - ")
                gantt_data.append({
                    "Task": f"{row['Employee']} ({row['Shift']})",
                    "Start": datetime.strptime(start_lunch, "%H:%M"),
                    "Finish": datetime.strptime(end_lunch, "%H:%M"),
                    "Category": "Lunch",  # Lunch is now a distinct category
                    "Type": "Lunch"
                })
            except ValueError:
                st.warning(f"Invalid lunch format for {row['Employee']}: {row['Lunch']}")

    gantt_df = pd.DataFrame(gantt_data)

    # Ensure the Gantt chart only renders if there is valid data
    if not gantt_df.empty:
        # Create a properly stacked Gantt Chart with selectable shift categories
        fig = px.timeline(
            gantt_df, 
            x_start="Start", 
            x_end="Finish", 
            y="Task",  # Now, each employee gets their own row
            color="Type",  # Work, Break, and Lunch are separate and selectable
            title="Weekly Shift Plan with Selectable Shifts, Breaks & Lunch"
        )

        # Ensure shift categories, breaks, and lunch are visible in the legend
        fig.update_traces(marker=dict(opacity=0.9))  # Adjust opacity to prevent overlaps
        fig.update_layout(barmode="overlay")  # Ensure breaks & lunch are layered visibly

        # Ensure tasks are sorted correctly
        fig.update_yaxes(categoryorder="total ascending")  
        fig.update_layout(
            xaxis_title="Time", 
            yaxis_title="Employees",
            showlegend=True,
            height=1000,  # Increased height for better readability
        )

        # Display Gantt chart
        st.subheader("Detailed Weekly Shift Plan (Selectable Shifts, Breaks & Lunch)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No schedule data available to display.")