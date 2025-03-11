import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Define shift structure & break rules
shifts = {
    "Toronto (8 AM - 4 PM)": {"start": 8, "end": 16, "break_slots": [(9.5, 9.75), (13.5, 13.75)], "lunch_range": (11.5, 13)},
    "Toronto (10 AM - 6 PM)": {"start": 10, "end": 18, "break_slots": [(11, 11.25), (15, 15.25)], "lunch_range": (12.5, 14)},
    "Bogotá (7 AM - 4:30 PM)": {"start": 7, "end": 16.5, "break_slots": [(9, 9.5)], "lunch_range": (11.5, 13.5)},
    "Bogotá (8:30 AM - 6 PM)": {"start": 8.5, "end": 18, "break_slots": [(10, 10.5)], "lunch_range": (12, 14)}
}

# Sidebar input
st.sidebar.header("Step 1: Enter Employees Per Shift")
employees_per_shift = {
    shift: st.sidebar.number_input(f"{shift}", min_value=0, step=1, value=3)
    for shift in shifts.keys()
}

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
            assigned_breaks = [f"{break_intervals[j][i]} - {round(break_intervals[j][i] + 0.25, 2)}" for j in range(len(break_slots))]
            assigned_lunch = f"{lunch_intervals[i]} - {round(lunch_intervals[i] + 0.5, 1)}"

            schedule_data.append([
                shift, f"Employee {i+1}", shift_info["start"], shift_info["end"],
                ", ".join(assigned_breaks), assigned_lunch
            ])

    df_schedule = pd.DataFrame(schedule_data, columns=["Shift", "Employee", "Start Time", "End Time", "Breaks", "Lunch"])

    # Store in session state for modifications
    if "df_schedule" not in st.session_state:
        st.session_state.df_schedule = df_schedule.copy()

# If a schedule exists, show it with live adjustments
if "df_schedule" in st.session_state:
    st.subheader("Step 2: Adjust Shifts, Breaks & Lunch Live")

    df_schedule = st.session_state.df_schedule

    adjusted_data = []
    for i in range(len(df_schedule)):
        shift_info = shifts[df_schedule.at[i, "Shift"]]
        min_start, max_end = shift_info["start"], shift_info["end"]
        lunch_start, lunch_end = shift_info["lunch_range"]

        col1, col2, col3 = st.columns(3)

        # Shift timing sliders on one row
        with col1:
            df_schedule.at[i, "Start Time"] = st.slider(
                f"Start ({df_schedule.at[i, 'Employee']})",
                min_value=float(min_start), max_value=float(max_end - 1), step=0.5, value=float(df_schedule.at[i, "Start Time"])
            )

        with col2:
            df_schedule.at[i, "End Time"] = st.slider(
                f"End ({df_schedule.at[i, 'Employee']})",
                min_value=float(df_schedule.at[i, "Start Time"] + 1),
                max_value=float(max_end), step=0.5, value=float(df_schedule.at[i, "End Time"])
            )

        with col3:
            lunch_time = float(df_schedule.at[i, "Lunch"].split("-")[0].strip())
            new_lunch_time = st.slider(
                f"Lunch ({df_schedule.at[i, 'Employee']})",
                min_value=float(lunch_start), max_value=float(lunch_end - 0.5), step=0.5, value=float(lunch_time)
            )
            df_schedule.at[i, "Lunch"] = f"{new_lunch_time} - {round(new_lunch_time + 0.5, 1)}"

        adjusted_data.append([
            df_schedule.at[i, "Shift"],
            df_schedule.at[i, "Employee"],
            df_schedule.at[i, "Start Time"],
            df_schedule.at[i, "End Time"],
            df_schedule.at[i, "Lunch"]
        ])

    # Display final schedule
    st.subheader("Final Schedule with Adjustments")
    st.write(df_schedule)

    # Create Gantt chart data
    gantt_data = []
    for _, row in df_schedule.iterrows():
        gantt_data.append(dict(Task=row["Employee"], Start=row["Start Time"], Finish=row["End Time"], Shift=row["Shift"]))

    gantt_df = pd.DataFrame(gantt_data)

    # Create Gantt Chart
    fig = px.timeline(gantt_df, x_start="Start", x_end="Finish", y="Task", color="Shift", title="Weekly Shift Plan")
    fig.update_yaxes(categoryorder="total ascending")  # Sort by time
    fig.update_layout(xaxis_title="Time", yaxis_title="Employees", showlegend=True)

    st.subheader("Weekly Plan Visualization")
    st.plotly_chart(fig, use_container_width=True)

    # Export updated schedule as Excel
    excel_file = "updated_schedule.xlsx"
    df_schedule.to_excel(excel_file, index=False)

    # Provide download button
    with open(excel_file, "rb") as f:
        st.download_button("Download Updated Schedule as Excel", f, file_name=excel_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")