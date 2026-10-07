import streamlit as st
import pandas as pd
from smart_gym_core import SmartGymSystem, calculate_bmi

st.set_page_config(
    page_title="Smart Gym Flow: Dual Portal & Set Sharing",
    page_icon="🏋️",
    layout="wide"
)

# Custom Styling (Inspired by premium fitness apps)
st.markdown("""
<style>
    .portal-header {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 1px solid #4338ca;
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 20px;
    }
    .bmi-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 16px;
        border: 1px solid #334155;
        margin-bottom: 14px;
    }
    .workout-step-card {
        background: #0f172a;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 5px solid #3b82f6;
        margin-bottom: 14px;
        border-top: 1px solid #1e293b;
        border-right: 1px solid #1e293b;
        border-bottom: 1px solid #1e293b;
    }
    .working-in-card {
        background: linear-gradient(135deg, #1e293b 0%, #1f2937 100%);
        border-left: 5px solid #f59e0b;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .badge-pill {
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-working-in { background-color: #78350f; color: #fde68a; }
    .badge-direct { background-color: #064e3b; color: #6ee7b7; }
</style>
""", unsafe_allow_html=True)

# Maintain persistent state for Gym System
if "gym_system" not in st.session_state:
    st.session_state["gym_system"] = SmartGymSystem()

gym = st.session_state["gym_system"]

# =========================================================================
# TOP LEVEL ROLE SELECTION (TWO DISTINCT PORTALS)
# =========================================================================
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
    <h2 style="margin: 0; color: #f8fafc;">🏋️ Smart Gym: AI Floor & Workout Coordinator</h2>
    <span style="color: #94a3b8; font-size: 14px;">Multi-User Set Sharing & Zero-Hardware Dispatch</span>
</div>
""", unsafe_allow_html=True)

selected_portal = st.radio(
    "Choose Your Login Portal:",
    ["👤 Gym Member Portal (Home Workout Assessment & Daily Route)", "🏢 Gym Owner Portal (Equipment Fleet, Hours & Live Floor)"],
    horizontal=True
)

st.divider()

# =========================================================================
# PORTAL 1: GYM OWNER PORTAL
# =========================================================================
if "Gym Owner" in selected_portal:
    st.markdown(f"""
    <div class="portal-header">
        <h3 style="margin: 0; color: #c7d2fe;">🏢 Gym Owner Administration: {gym.gym_name}</h3>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 14px;">
            Manage equipment names & physical stations, configure gym open/close hours, and monitor live multi-user floor capacity.
        </p>
    </div>
    """, unsafe_allow_html=True)

    owner_tab1, owner_tab2, owner_tab3 = st.tabs([
        "⚙️ Equipment Fleet & Stations", 
        "⏰ Gym Working Hours", 
        "📊 Live Floor Utility & 'Working In' Monitor"
    ])

    # Tab 1: Equipment Fleet Management
    with owner_tab1:
        st.write("#### 🏋️ Current Gym Equipment Catalog")
        st.caption("Each equipment type has physical stations (e.g. Bench Press #1, Bench Press #2) and backup swap alternatives.")

        fleet_data = []
        for eq in gym.equipment_fleet:
            fleet_data.append({
                "Equipment Name": eq["name"],
                "Category": eq["category"],
                "Total Stations": eq["quantity"],
                "Physical Stations": ", ".join(eq["stations"]),
                "Alternative Swap": eq["swap_alternative"],
                "Status": eq["status"]
            })
        st.dataframe(pd.DataFrame(fleet_data), use_container_width=True, hide_index=True)

        st.write("---")
        st.write("#### ➕ Add New Equipment to Gym")
        with st.form("add_eq_form"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                new_eq_name = st.text_input("Equipment Name", "Pec Fly Machine")
            with c2:
                new_eq_cat = st.selectbox("Category", ["Chest", "Legs", "Back", "Full Body", "Cardio"])
            with c3:
                new_eq_qty = st.number_input("Number of Stations", min_value=1, max_value=8, value=1)
            with c4:
                new_eq_swap = st.text_input("Swap Alternative Machine", "Cable Crossover Station")
            submit_new_eq = st.form_submit_button("Add Machine to Floor", type="primary")

        if submit_new_eq:
            gym.add_equipment(new_eq_name, new_eq_cat, int(new_eq_qty), new_eq_swap)
            st.success(f"Added **{new_eq_name}** ({new_eq_qty} stations) to {gym.gym_name} inventory!")
            st.rerun()

    # Tab 2: Operating Schedule & Peak Hours
    with owner_tab2:
        st.write("#### ⏰ Gym Operating Hours & Peak Traffic Configuration")
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            open_h = st.selectbox("Gym Opening Time", ["05:00 AM", "06:00 AM", "07:00 AM"], index=1)
            close_h = st.selectbox("Gym Closing Time", ["09:00 PM", "10:00 PM", "11:00 PM", "12:00 AM"], index=1)
            if st.button("Save Operating Hours"):
                gym.update_gym_schedule(open_h, close_h)
                st.success("Gym operating hours updated successfully!")
        with col_h2:
            st.info("""
            **Peak Hours Policy:**
            - **Morning Rush:** 07:30 AM - 09:00 AM
            - **Evening Rush:** 05:30 PM - 07:30 PM
            
            *During peak rush, the AI automatically activates **'Working-In' (Active Rest Set Sharing)** to allow 2 lifters per heavy station, cutting wait times to 0!*
            """)

    # Tab 3: Live Floor Utilization & Working In Monitor
    with owner_tab3:
        st.write("#### 📊 Live Floor Timetable & Equipment Sharing Monitor")
        schedule_data = gym.build_smart_floor_schedule()

        # KPIs
        kp1, kp2, kp3, kp4 = st.columns(4)
        active_stations = sum(eq["quantity"] for eq in gym.equipment_fleet if eq["status"] == "Active")
        kp1.metric("Active Physical Stations", active_stations)
        kp2.metric("Registered Members", len(gym.members))
        kp3.metric("Peak Rush Window", "08:00 AM - 09:00 AM")
        kp4.metric("Set-Sharing 'Working In' Sessions", len(schedule_data["working_in_pairings"]), delta="Capacity Doubled on Shared Gear", delta_color="normal")

        st.divider()

        # Highlights of Working In Pairings
        if schedule_data["working_in_pairings"]:
            st.write("##### 🤝 Active 'Working In' (Rest-Set Sharing) Pairings Today")
            for pair in schedule_data["working_in_pairings"]:
                st.markdown(f"""
                <div class="working-in-card">
                    <b style="color: #fde68a;">Station: {pair['station']} at {pair['time']}</b><br>
                    Co-Lifters: <span style="color: #60a5fa; font-weight: bold;">{pair['lifter_1']}</span> & 
                    <span style="color: #38bdf8; font-weight: bold;">{pair['lifter_2']}</span><br>
                    <span style="color: #cbd5e1; font-size: 13px;">👉 {pair['reason']}</span>
                </div>
                """, unsafe_allow_html=True)

        st.write("##### 🗓️ Station Reservation Timetable (Hour-by-Hour)")
        time_pick = st.selectbox("View Time Window:", ["Morning Rush (08:00 AM - 08:45 AM)", "Evening Rush (06:00 PM - 06:45 PM)"])
        
        display_slots = ["08:00 AM", "08:15 AM", "08:30 AM", "08:45 AM"] if "Morning" in time_pick else ["06:00 PM", "06:15 PM", "06:30 PM", "06:45 PM"]

        table_rows = []
        for station_name, slots in schedule_data["station_grid"].items():
            row = {"Station": station_name}
            for s in display_slots:
                occupants = slots.get(s, [])
                if len(occupants) == 2:
                    row[s] = f"🤝 {occupants[0]} & {occupants[1]} (Working In)"
                elif len(occupants) == 1:
                    row[s] = f"👤 {occupants[0]}"
                else:
                    row[s] = "🟢 Free"
            table_rows.append(row)

        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)


# =========================================================================
# PORTAL 2: GYM MEMBER PORTAL (Home Workout App Biometrics & Schedule)
# =========================================================================
else:
    st.markdown(f"""
    <div class="portal-header">
        <h3 style="margin: 0; color: #93c5fd;">👤 Member Fitness & Workout Portal: {gym.gym_name}</h3>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 14px;">
            Personalized biometric intake (BMI, Height, Weight) + tailored sets, reps, and zero-wait station routing.
        </p>
    </div>
    """, unsafe_allow_html=True)

    member_tab1, member_tab2 = st.tabs([
        "📋 Daily Check-In & Biometrics (Home Workout Style)", 
        "🏋️ Today's Workout & Shared Set Timer"
    ])

    # Tab 1: Biometric Intake & Daily Time Picker
    with member_tab1:
        st.write("#### 📝 Member Physical Profile & Daily Time Booking")
        st.caption("Inspired by top fitness apps: We calculate your BMI and tailor your reps, sets, and arrival time.")

        existing_names = [m["name"] for m in gym.members]
        member_select_mode = st.radio("Are you logging in or creating a new profile?", ["Existing Member", "🌱 New Member / Fresher Registration"], horizontal=True)

        if member_select_mode == "Existing Member":
            selected_member_name = st.selectbox("Select Your Profile:", existing_names, index=0)
            active_member = next((m for m in gym.members if m["name"] == selected_member_name), gym.members[0])
            init_gender = active_member["gender"]
            init_age = active_member["age"]
            init_height = float(active_member["height_cm"])
            init_weight = float(active_member["weight_kg"])
            init_goal = active_member["goal"]
            init_exp = active_member["experience"]
            init_time = active_member["today_arrival_time"]
            init_muscle = active_member.get("focus_muscle", "Chest")
        else:
            selected_member_name = "New Athlete"
            init_gender = "Male"
            init_age = 25
            init_height = 175.0
            init_weight = 70.0
            init_goal = "Bodybuilding (Muscle Mass)"
            init_exp = "Beginner (Fresher)"
            init_time = "08:00 AM"
            init_muscle = "Chest"

        with st.form("biometric_form"):
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                mem_name = st.text_input("Your Full Name", selected_member_name if member_select_mode == "Existing Member" else "")
                mem_gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(init_gender))
                mem_age = st.number_input("Age", min_value=14, max_value=85, value=init_age)
                mem_height = st.slider("Height (cm)", min_value=130.0, max_value=220.0, value=init_height, step=0.5)
                mem_weight = st.slider("Weight (kg)", min_value=35.0, max_value=160.0, value=init_weight, step=0.5)
            
            with b_col2:
                mem_goal = st.selectbox(
                    "Primary Fitness Goal:",
                    ["Bodybuilding (Muscle Mass)", "Fat Loss & Lean Definition", "Strength & Power (Powerlifting)", "General Fitness & Toning"],
                    index=["Bodybuilding (Muscle Mass)", "Fat Loss & Lean Definition", "Strength & Power (Powerlifting)", "General Fitness & Toning"].index(init_goal)
                )
                mem_exp = st.selectbox(
                    "Experience Level:",
                    ["Beginner (Fresher)", "Intermediate", "Advanced"],
                    index=["Beginner (Fresher)", "Intermediate", "Advanced"].index(init_exp)
                )
                mem_time = st.selectbox(
                    "⏰ What is your free gym time today? (Within gym hours 06:00 AM - 10:00 PM)",
                    ["06:00 AM", "07:00 AM", "08:00 AM", "08:15 AM", "08:30 AM", "09:00 AM", "05:00 PM", "05:30 PM", "06:00 PM", "06:30 PM", "07:00 PM"],
                    index=["06:00 AM", "07:00 AM", "08:00 AM", "08:15 AM", "08:30 AM", "09:00 AM", "05:00 PM", "05:30 PM", "06:00 PM", "06:30 PM", "07:00 PM"].index(init_time)
                )
                mem_muscle = st.selectbox(
                    "Target Muscle Group for Today:",
                    ["Chest", "Legs", "Back", "Full Body"],
                    index=["Chest", "Legs", "Back", "Full Body"].index(init_muscle)
                )
                mem_duration = st.select_slider("Workout Duration Today:", options=[30, 45, 60], value=45, format_func=lambda x: f"{x} Mins")

            submit_bio = st.form_submit_button("💾 Save Profile & Generate Smart Workout", type="primary")

        if submit_bio and mem_name.strip():
            updated_m = gym.register_or_update_member(
                name=mem_name.strip(),
                gender=mem_gender,
                age=int(mem_age),
                height_cm=float(mem_height),
                weight_kg=float(mem_weight),
                goal=mem_goal,
                experience=mem_exp,
                arrival_time=mem_time,
                duration_mins=int(mem_duration),
                focus_muscle=mem_muscle
            )
            st.success(f"Profile saved for **{mem_name}**! Switch to the 'Today's Workout' tab to view your route.")
            st.rerun()

        # Display Live BMI Calculation Card
        bmi_val, bmi_cat, bmi_color = calculate_bmi(init_height, init_weight)
        st.write("---")
        st.write("#### 🩺 Instant Biometric Assessment")
        st.markdown(f"""
        <div class="bmi-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #94a3b8; font-size: 14px;">Calculated Body Mass Index (BMI):</span>
                <span style="font-size: 24px; font-weight: bold; color: {bmi_color};">{bmi_val}</span>
            </div>
            <div style="margin-top: 6px; font-size: 15px; color: #f8fafc;">
                Classification: <b style="color: {bmi_color};">{bmi_cat}</b>
            </div>
            <p style="margin: 8px 0 0 0; color: #94a3b8; font-size: 13px;">
                💡 <b>Smart Prescription Impact:</b> Rep ranges, sets, and rest times for your workout below have been calibrated automatically to this biometric rating.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Tab 2: Today's Workout & Working In Assistant
    with member_tab2:
        # Get active member
        current_names = [m["name"] for m in gym.members]
        active_user_name = st.selectbox("Viewing Workout For Member:", current_names, index=0)
        user_obj = next((m for m in gym.members if m["name"] == active_user_name), gym.members[0])

        floor_schedule = gym.build_smart_floor_schedule()
        user_plan = floor_schedule["member_workout_plans"].get(active_user_name)

        st.write(f"### 🏋️ {active_user_name}'s Tailored Workout for {user_obj.get('today_arrival_time', '08:00 AM')}")
        st.caption(f"Goal: **{user_obj['goal']}** | Level: **{user_obj['experience']}** | Target: **{user_obj.get('focus_muscle', 'Chest')}**")

        if user_plan and user_plan["steps"]:
            for step in user_plan["steps"]:
                is_working_in = step["is_working_in"]
                partner = step.get("partner_name")

                card_class = "working-in-card" if is_working_in else "workout-step-card"
                badge_html = (
                    f"<span class='badge-pill badge-working-in'>🤝 Working In with {partner} (Active Rest Sharing)</span>"
                    if is_working_in 
                    else "<span class='badge-pill badge-direct'>🟢 Direct Station Access</span>"
                )

                st.markdown(f"""
                <div class="{card_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; color: #f8fafc;">Exercise {step['step_num']}: {step['equipment_name']}</h4>
                        {badge_html}
                    </div>
                    <div style="margin: 6px 0; color: #38bdf8; font-weight: 600; font-size: 16px;">
                        👉 Station: {step['station']} &nbsp;|&nbsp; ⏰ {step['time_window']}
                    </div>
                    <div style="display: flex; gap: 20px; color: #e2e8f0; font-size: 15px; margin: 8px 0;">
                        <div>🎯 <b>Sets:</b> {step['sets']} Sets</div>
                        <div>🔁 <b>Reps:</b> {step['reps']}</div>
                        <div>⏱️ <b>Rest Between Sets:</b> {step['rest_seconds']} seconds</div>
                    </div>
                    <div style="color: #94a3b8; font-size: 13px; margin-top: 6px;">
                        💡 <b>Coach Note:</b> {step['coach_notes']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # If "Working In", display interactive shared set timer!
                if is_working_in:
                    with st.expander(f"⏱️ Launch Shared Set & Rest Assistant (Working in with {partner})", expanded=True):
                        st.write(f"**How You & {partner} Share {step['station']} with Zero Waiting:**")
                        st.markdown(f"""
                        1. **Set 1:** Lifter 1 (**{partner}**) performs 10 reps (~45s) while you (**{active_user_name}**) rest & spot.
                        2. **Switch:** While {partner} rests for 90 seconds, **you perform your Set 1**!
                        3. **Repeat:** Alternate sets until both complete all {step['sets']} sets.
                        """)
                        
                        col_timer1, col_timer2 = st.columns(2)
                        with col_timer1:
                            if st.button(f"🏁 Complete Set on {step['station']}", key=f"set_btn_{step['step_num']}"):
                                st.toast(f"Great set! Now resting {step['rest_seconds']}s while {partner} takes their turn.", icon="💪")
                        with col_timer2:
                            st.caption(f"Partner status: **{partner} is ready for their set.**")

        else:
            st.info("No workout steps found. Please check your arrival time in the profile tab.")
