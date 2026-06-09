import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz  # Timezone thik korar jonne
from streamlit_qrcode_scanner import qrcode_scanner

# Timezone Kolkata set kora holo (Real-time vul dekhabe na)
KOLKATA_TZ = pytz.timezone("Asia/Kolkata")

ATTENDANCE_FILE = "showroom_attendance.csv"
USER_FILE = "showroom_users.csv"

# Shroom er nijossho fixed QR content (Jeta print out kore showroom a lagano thakbe)
SHOWROOM_QR_SECRET = "JK_SUZUKI_SHOWROOM_OFFICIAL_ATTENDANCE_2026"

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

# Salary Calculation Logic (4 din chuti bad e katar jonne)
def calculate_emp_salary(emp_id, base_salary, att_dataframe):
    # Total month days = 30 dhorলাম আপাতত
    total_days = 30 
    allowed_holidays = 4 # Mas e 4 te chuti fix, payment katbe na
    
    # Employee koydin present chilo ta check
    emp_logs = att_dataframe[att_dataframe["ID"] == str(emp_id)]
    present_days = emp_logs["Date"].nunique() if not emp_logs.empty else 0
    
    # Paid days = Present days + 4 din chuti (Kintu total month days er beshi hote parbe na)
    paid_days = min(present_days + allowed_holidays, total_days)
    absent_days = max(0, total_days - paid_days)
    
    # Salary calculation
    per_day_salary = base_salary / total_days
    payable_salary = round(paid_days * per_day_salary, 2)
    deduction = round(absent_days * per_day_salary, 2)
    
    return present_days, allowed_holidays, absent_days, payable_salary, deduction

att_df, user_df = load_data()

st.set_page_config(page_title="JK Suzuki Management", layout="wide")
st.title("🏍️ JK Suzuki Attendance & Salary System")
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

else:
    # Sidebar Profile & Logout
    st.sidebar.subheader(f"👤 Profile: {st.session_state.user_name}")
    st.sidebar.write(f"**ID No:** {st.session_state.user_id}")
    st.sidebar.write(f"**Role:** {st.session_state.user_role}")
    
    # Employee der nijeder profile a live salary & chuti dekhano holo
    if st.session_state.user_role == "Employee":
        emp_info = user_df[user_df["ID"] == st.session_state.user_id]
        base_sal = emp_info.iloc[0]["Base_Salary"]
        p_days, h_days, a_days, p_sal, ded = calculate_emp_salary(st.session_state.user_id, base_sal, att_df)
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("💰 Your Live Salary Report")
        st.sidebar.write(f"**Base Salary:** ₹{base_sal}")
        st.sidebar.write(f"**Present Today:** {p_days} Days")
        st.sidebar.write(f"**Monthly Offs:** {h_days} Days (Paid)")
        st.sidebar.write(f"**Absent Days:** {a_days} Days (Unpaid)")
        st.sidebar.success(f"**Current Payable:** ₹{p_sal}")
        if ded > 0:
            st.sidebar.error(f"**Deduction (Absence):** -₹{ded}")

    if st.sidebar.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.user_id = ""
        st.session_state.user_name = ""
        st.session_state.user_role = ""
        st.rerun()
        
    st.sidebar.markdown("---")

    # ==================== 1. Employee Screen (Strict Live QR Scanner) ====================
    if st.session_state.user_role == "Employee":
        st.subheader("📷 Shroom Live Attendance Scanner")
        
        # Kolkata TZ onujayi real time exact thik kora holo
        now_kolkata = datetime.now(KOLKATA_TZ)
        current_date = str(now_kolkata.date())
        current_time = now_kolkata.strftime("%I:%M %p")
        
        st.info(f"📅 **Today's Date:** {current_date} | ⏰ **Kolkata Time:** {current_time}")
        
        current_user_id = str(st.session_state.user_id).strip()
        today_entry = att_df[(att_df["Date"] == current_date) & (att_df["ID"] == current_user_id)]
        
        if today_entry.empty:
            st.warning("📋 আপনার আজকের হাজিরা দেওয়া হয়নি। শোরুমের দেওয়ালে থাকা QR Code টি নিচের লাইভ ক্যামেরার সামনে ধরুন। (গ্যালারি থেকে স্ক্যান হবে না)")
            
            # Camera on hobe, gallery select korar option thakbe na
            qr_code_value = qrcode_scanner(key='qr_scanner_entry')
            
            if qr_code_value:
                if qr_code_value == SHOWROOM_QR_SECRET:
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
                    st.success("✅ ENTRY Recorded Successfully via Live Scan!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ ভুল QR Code! দয়া করে শোরুমের আসল QR Code টি স্ক্যান করুন।")
                    
        elif today_entry.iloc[0]["Exit Time"] == "Not Out Yet":
            st.info("⚠️ আপনার ENTRY করা আছে। ছুটির সময় বিদায় নেওয়ার জন্য আবার শোরুমের QR Code টি লাইভ স্ক্যান করুন।")
            
            qr_code_value = qrcode_scanner(key='qr_scanner_exit')
            
            if qr_code_value:
                if qr_code_value == SHOWROOM_QR_SECRET:
                    idx = att_df[(att_df["Date"] == current_date) & (att_df["ID"] == current_user_id)].index
                    att_df.loc[idx, "Exit Time"] = current_time
                    save_attendance(att_df)
                    st.success("✅ EXIT Recorded Successfully! Have a good day.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ ভুল QR Code! দয়া করে শোরুমের আসল QR Code টি স্ক্যান করুন।")
        else:
            st.success("🎉 Today's Attendance Completed! (Entry & Exit Both Recorded)")
            
        st.markdown("---")
        st.subheader("📊 Your Attendance History")
        my_history = att_df[att_df["ID"] == current_user_id]
        if not my_history.empty:
            st.dataframe(my_history, use_container_width=True)
        else:
            st.info("No attendance history found for you yet.")

    # ==================== 2. Admin Screen ====================
    elif st.session_state.user_role == "Admin":
        st.subheader("👑 Owner / Admin Control Panel")
        
        # Admin can view or print the QR code from here
        with st.expander("🖨️ Showroom Official QR Code (Print & Paste This)"):
            st.write("নিচের এই কিউআর কোডটি বড় করে স্ক্রিনশট নিন অথবা প্রিন্ট করে শোরুমের দেওয়ালে বা গেটে লাগিয়ে দিন।")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={SHOWROOM_QR_SECRET}", caption="JK Suzuki Official QR Code")
        
        search_id = st.text_input("🔍 Type Employee ID No to Search Profile & Salary:", placeholder="e.g. 101").strip()
        
        if search_id != "":
            emp_info = user_df[user_df["ID"] == str(search_id)]
            
            if not emp_info.empty:
                emp_name = emp_info.iloc[0]["Name"]
                base_sal = emp_info.iloc[0]["Base_Salary"]
                role = emp_info.iloc[0]["Role"]
                
                st.success(f"👤 Employee Profile Found: **{emp_name}** (Role: {role})")
                
                # Calculate Salary with 4 holidays logic
                p_days, h_days, a_days, p_sal, ded = calculate_emp_salary(search_id, base_sal, att_df)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"📅 Attendance Logs for {emp_name}")
                    emp_att = att_df[att_df["ID"] == str(search_id)]
                    if not emp_att.empty:
                        st.dataframe(emp_att, use_container_width=True)
                    else:
                        st.info("This employee hasn't recorded any attendance yet.")
                        
                with col2:
                    st.subheader("💰 Live Absent-Based Salary Status")
                    st.metric("Total Present Days", f"{p_days} Days")
                    st.metric("Allowed Paid Offs (4 Chuti)", f"{h_days} Days")
                    st.metric("Absent Days (Money Cut)", f"{a_days} Days")
                    st.metric("Base Monthly Salary", f"₹ {base_sal}")
                    st.error(f"Absence Deduction: -₹ {ded}")
                    st.subheader(f"💵 Net Payable Salary: ₹ {p_sal}")
            else:
                st.error("No employee found with this ID No!")
                
        st.markdown("---")
        st.subheader("📋 Overall Live Attendance Dashboard (All Employees)")
        
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
