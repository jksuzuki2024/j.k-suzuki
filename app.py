import streamlit as st
import pandas as pd
import os
from datetime import datetime

# File gulor nam
ATTENDANCE_FILE = "showroom_attendance.csv"
USER_FILE = "showroom_users.csv"

# Prathomik employee list
DEFAULT_USERS = pd.DataFrame([
    {"ID": "101", "Name": "Amit Kumar", "Password": "password101", "Role": "Employee", "Base_Salary": 15000},
    {"ID": "102", "Name": "Rahul Singh", "Password": "password102", "Role": "Employee", "Base_Salary": 12000},
    {"ID": "admin", "Name": "Showroom Owner", "Password": "admin786", "Role": "Admin", "Base_Salary": 0}
])

def load_data():
    if os.path.exists(ATTENDANCE_FILE):
        try:
            att_df = pd.read_csv(ATTENDANCE_FILE)
            att_df["ID"] = att_df["ID"].astype(str).str.strip()
            att_df["Date"] = att_df["Date"].astype(str).str.strip()
        except:
            att_df = pd.DataFrame(columns=["Date", "ID", "Name", "Entry Time", "Exit Time", "Status"])
    else:
        att_df = pd.DataFrame(columns=["Date", "ID", "Name", "Entry Time", "Exit Time", "Status"])
        
    if os.path.exists(USER_FILE):
        user_df = pd.read_csv(USER_FILE)
        user_df["ID"] = user_df["ID"].astype(str).str.strip()
    else:
        user_df = DEFAULT_USERS
        user_df["ID"] = user_df["ID"].astype(str).str.strip()
        user_df.to_csv(USER_FILE, index=False)
        
    return att_df, user_df

def save_attendance(df):
    df.to_csv(ATTENDANCE_FILE, index=False)

def save_users(df):
    df.to_csv(USER_FILE, index=False)

att_df, user_df = load_data()

st.set_page_config(page_title="JK Suzuki Management", layout="wide")
st.title("🏬 JK Suzuki Attendance & Salary System")
st.markdown("---")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = ""
    st.session_state.user_name = ""
    st.session_state.user_role = ""

# Login Screen
if not st.session_state.logged_in:
    st.subheader("🔒 User Login")
    col1, col2 = st.columns(2)
    with col1:
        login_id = st.text_input("Enter your ID No:").strip()
    with col2:
        login_pass = st.text_input("Enter Password:", type="password").strip()
        
    if st.button("Login", type="primary"):
        match = user_df[(user_df["ID"] == str(login_id)) & (user_df["Password"] == str(login_pass))]
        if not match.empty:
            st.session_state.logged_in = True
            st.session_state.user_id = str(match.iloc[0]["ID"])
            st.session_state.user_name = match.iloc[0]["Name"]
            st.session_state.user_role = match.iloc[0]["Role"]
            st.success(f"Welcome {st.session_state.user_name}!")
            st.rerun()
        else:
            st.error("Invalid ID or Password! Please try again.")

# Login hobar por
else:
    st.sidebar.subheader(f"👤 Profile: {st.session_state.user_name}")
    st.sidebar.write(f"**ID No:** {st.session_state.user_id}")
    st.sidebar.write(f"**Role:** {st.session_state.user_role}")
    
    if st.sidebar.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.user_id = ""
        st.session_state.user_name = ""
        st.session_state.user_role = ""
        st.rerun()

    st.sidebar.markdown("---")

    # ==================== 1. Employee Screen ====================
    if st.session_state.user_role == "Employee":
        st.subheader("🕒 Your Daily Attendance")
        
        current_date = str(datetime.now().date())
        current_time = datetime.now().strftime("%I:%M %p")
        
        st.info(f"📅 Today's Date: **{current_date}** | ⏰ Current Time: **{current_time}**")
        
        # dynamic current user check
        current_user_id = str(st.session_state.user_id).strip()
        today_entry = att_df[(att_df["Date"] == current_date) & (att_df["ID"] == current_user_id)]
        
        c1, c2 = st.columns(2)
        
        if today_entry.empty:
            with c1:
                if st.button("📥 Press for ENTRY", use_container_width=True, type="primary"):
                    new_row = {
                        "Date": current_date,
                        "ID": current_user_id,
                        "Name": st.session_state.user_name,
                        "Entry Time": current_time,
                        "Exit Time": "Not Out Yet",
                        "Status": "Present"
                    }
                    att_df = pd.concat([att_df, pd.DataFrame([new_row])], ignore_index=True)
                    save_attendance(att_df)
                    st.success(f"Entry recorded automatically at {current_time}!")
                    st.rerun()
            with c2:
                st.info("You need to log Entry first before Exit.")
                
        elif str(today_entry.iloc[0]["Exit Time"]) == "Not Out Yet":
            with c1:
                st.warning(f"✅ Your Entry is recorded today at: {today_entry.iloc[0]['Entry Time']}")
            with c2:
                if st.button("📤 Press for EXIT", use_container_width=True, type="secondary"):
                    idx = att_df[(att_df["Date"] == current_date) & (att_df["ID"] == current_user_id)].index
                    att_df.loc[idx, "Exit Time"] = current_time
                    save_attendance(att_df)
                    st.success(f"Exit recorded automatically at {current_time}!")
                    st.rerun()
        else:
            st.success(f"🎉 Today's Attendance Completed! (Entry: {today_entry.iloc[0]['Entry Time']} | Exit: {today_entry.iloc[0]['Exit Time']})")
            st.balloons()

        st.markdown("---")
        st.subheader("📊 Your Attendance History")
        my_history = att_df[att_df["ID"] == current_user_id]
        if not my_history.empty:
            st.dataframe(my_history, use_container_width=True)
        else:
            st.info("No attendance history found for you yet.")

    # ==================== 2. Admin Screen ====================
    elif st.session_state.user_role == "Admin":
        st.subheader("🔑 Owner / Admin Control Panel")
        
        search_id = st.text_input("🔍 Type Employee ID No to Search Profile & Salary:", placeholder="e.g. 101").strip()
        
        if search_id != "":
            emp_info = user_df[user_df["ID"] == str(search_id)]
            
            if not emp_info.empty:
                emp_name = emp_info.iloc[0]["Name"]
                base_sal = emp_info.iloc[0]["Base_Salary"]
                role = emp_info.iloc[0]["Role"]
                
                st.success(f"👤 Employee Profile Found: **{emp_name}** (Role: {role})")
                
                emp_att = att_df[att_df["ID"] == str(search_id)]
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"📊 Attendance Logs for {emp_name}")
                    if not emp_att.empty:
                        st.dataframe(emp_att, use_container_width=True)
                    else:
                        st.info("This employee hasn't recorded any attendance yet.")
                        
                with col2:
                    st.subheader("💰 Salary Calculator")
                    total_days = st.number_input("Total Days in Month", min_value=1, max_value=31, value=30)
                    
                    if not emp_att.empty:
                        present_days = len(emp_att)
                        per_day_sal = base_sal / total_days
                        payable_salary = round(present_days * per_day_sal, 2)
                        
                        st.metric("Total Present Days", f"{present_days} Days")
                        st.metric("Base Monthly Salary", f"₹/৳ {base_sal}")
                        st.subheader(f"💵 Payable Salary: ₹/৳ {payable_salary}")
                    else:
                        st.metric("Total Present Days", "0 Days")
                        st.subheader("💵 Payable Salary: ₹/৳ 0.00")
            else:
                st.error("No employee found with this ID No!")
        
        st.markdown("---")
        st.subheader("📋 Overall Live Attendance Dashboard (All Employees)")
        
        # Master reset button only for testing
        if st.checkbox("Show Data Reset Option (Danger Zone)"):
            if st.button("Delete All Old Attendance Logs"):
                if os.path.exists(ATTENDANCE_FILE):
                    os.remove(ATTENDANCE_FILE)
                st.success("All old history deleted successfully!")
                st.rerun()

        if not att_df.empty:
            st.dataframe(att_df, use_container_width=True)
        else:
            st.info("No logs generated by any employee today.")
            
        with st.expander("➕ Click to Add New Employee Account"):
            new_id = st.text_input("New Employee ID:").strip()
            new_name = st.text_input("New Employee Name:").strip()
            new_pass = st.text_input("Set Password:").strip()
            new_sal = st.number_input("Monthly Salary:", min_value=0, value=12000)
            
            if st.button("Create Account"):
                if str(new_id) in user_df["ID"].values:
                    st.error("This ID already exists!")
                elif new_id=="" or new_name=="" or new_pass=="":
                    st.error("Please fill all fields!")
                else:
                    new_u = {"ID": str(new_id), "Name": new_name, "Password": new_pass, "Role": "Employee", "Base_Salary": new_sal}
                    user_df = pd.concat([user_df, pd.DataFrame([new_u])], ignore_index=True)
                    save_users(user_df)
                    st.success(f"Account created successfully for {new_name} (ID: {new_id})!")
                    st.rerun()