import streamlit as st
import pandas as pd
from datetime import datetime
import os
import pytz
import io

# Timezone Kolkata
KOLKATA_TZ = pytz.timezone("Asia/Kolkata")
SHOWROOM_QR_SECRET = "JK_SUZUKI_SHOWROOM_OFFICIAL_ATTENDANCE_2026"

# Permanent Excel Database Path
DB_FILE = "employee_database.xlsx"
ATT_FILE = "attendance_database.xlsx"

# Initializing permanent local databases
def init_databases():
    fixed_accounts = {
        "admin": {"Name": "Showroom Owner", "Password": "admin786", "Role": "Admin", "Base_Salary": 0},
        "101": {"Name": "Amit Kumar", "Password": "password101", "Role": "Employee", "Base_Salary": 15000},
        "102": {"Name": "Rahul Singh", "Password": "password102", "Role": "Employee", "Base_Salary": 12000},
        "114": {"Name": "Jahir", "Password": "jahir", "Role": "Employee", "Base_Salary": 12000}
    }
    if not os.path.exists(DB_FILE):
        rows = [{"ID": str(k), "Name": v["Name"], "Password": str(v["Password"]), "Role": v["Role"], "Base_Salary": float(v["Base_Salary"])} for k, v in fixed_accounts.items()]
        pd.DataFrame(rows).to_excel(DB_FILE, index=False)
    
    if not os.path.exists(ATT_FILE):
        pd.DataFrame(columns=["Date", "ID", "Name", "Entry Time", "Exit Time", "Status"]).to_excel(ATT_FILE, index=False)

init_databases()

# Helper functions to read/write files (Fixes memory wipe on refresh)
def get_all_users():
    df = pd.read_excel(DB_FILE)
    return {str(row["ID"]).strip(): {"Name": row["Name"], "Password": str(row["Password"]).strip(), "Role": row["Role"], "Base_Salary": float(row["Base_Salary"])} for _, row in df.iterrows()}

def add_user_to_db(uid, name, password, base_salary):
    df = pd.read_excel(DB_FILE)
    new_row = pd.DataFrame([{"ID": str(uid).strip(), "Name": name, "Password": str(password).strip(), "Role": "Employee", "Base_Salary": float(base_salary)}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(DB_FILE, index=False)

def get_attendance():
    return pd.read_excel(ATT_FILE)

def save_attendance(df):
    df.to_excel(ATT_FILE, index=False)

# Salary Calculation (4 Allowed Weekly Paid Holidays)
def calculate_salary_report(emp_id, base_salary):
    total_days = 30
    allowed_holidays = 4
    df_att = get_attendance()
    
    if not df_att.empty:
        emp_logs = df_att[df_att["ID"].astype(str) == str(emp_id)]
        present_days = emp_logs["Date"].nunique()
    else:
        present_days = 0
        
    paid_days = min(present_days + allowed_holidays, total_days)
    absent_days = max(0, total_days - paid_days)
    
    per_day_salary = base_salary / total_days
    net_payable = round(paid_days * per_day_salary, 2)
    deduction = round(absent_days * per_day_salary, 2)
    
    return present_days, allowed_holidays, absent_days, net_payable, deduction

# App Configuration
st.set_page_config(page_title="JK Suzuki Systems", layout="wide")
st.title("🏍️ JK Suzuki Attendance & Salary Portal")
st.markdown("---")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = ""

all_users = get_all_users()

if not st.session_state.logged_in:
    st.subheader("🔒 User Login")
    col1, col2 = st.columns(2)
    with col1:
        login_id = st.text_input("Enter your ID No:").strip()
    with col2:
        login_pass = st.text_input("Enter Password:", type="password").strip()
        
    if st.button("Login", type="primary"):
        if login_id in all_users and str(all_users[login_id]["Password"]) == login_pass:
            st.session_state.logged_in = True
            st.session_state.user_id = login_id
            st.rerun()
        else:
            st.error("Invalid ID or Password!")
else:
    current_uid = st.session_state.user_id
    user_info = all_users[current_uid]
    
    st.sidebar.subheader(f"👤 {user_info['Name']}")
    st.sidebar.write(f"**ID:** {current_uid} | **Role:** {user_info['Role']}")
    if st.sidebar.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.rerun()
        
    # EMPLOYEE INTERFACE
    if user_info["Role"] == "Employee":
        p_days, h_days, a_days, p_sal, ded = calculate_salary_report(current_uid, user_info['Base_Salary'])
        
        st.subheader("📊 Your Live Salary & Attendance Sheet")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(label="Base Salary", value=f"₹{user_info['Base_Salary']}")
            st.write(f"💼 **Days Present:** {p_days}")
        with c2:
            st.metric(label="Net Payable (Salary)", value=f"₹{p_sal}")
            st.write(f"🌴 **Paid Leaves:** {h_days} Days (Given)")
        with c3:
            st.metric(label="Deducted (Absent)", value=f"-₹{ded}")
            st.write(f"❌ **Unpaid Absents:** {a_days}")
            
        st.markdown("---")
        st.subheader("📷 Shroom Attendance Scanner")
        from streamlit_qrcode_scanner import qrcode_scanner
        now_k = datetime.now(KOLKATA_TZ)
        c_date = str(now_k.date())
        c_time = now_k.strftime("%I:%M %p")
        st.info(f"📅 Date: {c_date} | ⏰ Time: {c_time}")
        
        df_att = get_attendance()
        today_entry = df_att[(df_att["Date"] == c_date) & (df_att["ID"].astype(str) == str(current_uid))]
        
        if today_entry.empty:
            st.warning("📋 আজকের হাজিরা দেওয়া হয়নি। শোরুমের QR Code স্ক্যান করুন।")
            val = qrcode_scanner(key='entry_scan')
            if val == SHOWROOM_QR_SECRET:
                new_row = pd.DataFrame([{"Date": c_date, "ID": str(current_uid), "Name": user_info['Name'], "Entry Time": c_time, "Exit Time": "Not Out Yet", "Status": "Present"}])
                save_attendance(pd.concat([df_att, new_row], ignore_index=True))
                st.success("✅ ENTRY Recorded!")
                st.rerun()
        elif today_entry.iloc[0]["Exit Time"] == "Not Out Yet":
            st.info("⚠️ ছুটির সময় বিদায় নেওয়ার জন্য আবার QR Code স্ক্যান করুন।")
            val = qrcode_scanner(key='exit_scan')
            if val == SHOWROOM_QR_SECRET:
                df_att.loc[(df_att["Date"] == c_date) & (df_att["ID"].astype(str) == str(current_uid)), "Exit Time"] = c_time
                save_attendance(df_att)
                st.success("✅ EXIT Recorded!")
                st.rerun()
        else:
            st.success("🎉 Today's Attendance Completed!")
            
        st.markdown("---")
        st.dataframe(df_att[df_att["ID"].astype(str) == str(current_uid)], use_container_width=True)

    # ADMIN INTERFACE
    elif user_info["Role"] == "Admin":
        st.subheader("👑 Owner Control Panel")
        
        with st.expander("➕ Add New Employee Account (নতুন কর্মচারী যোগ করুন)"):
            n_id = st.text_input("New Employee ID No:").strip()
            n_name = st.text_input("Employee Full Name:").strip()
            n_pass = st.text_input("Set Password:").strip()
            n_sal = st.number_input("Monthly Base Salary (₹):", min_value=0, value=12000)
            
            if st.button("Create Permanent Account", type="primary"):
                if n_id in all_users:
                    st.error("❌ ID already exists!")
                elif n_id=="" or n_name=="" or n_pass=="":
                    st.error("❌ Fill all fields!")
                else:
                    add_user_to_db(n_id, n_name, n_pass, n_sal)
                    st.success(f"✅ Account {n_id} created permanently in Excel Database!")
                    st.rerun()
                    
        st.markdown("---")
        df_att = get_attendance()
        if not df_att.empty:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                df_att.to_excel(writer, index=False, sheet_name='Sheet1')
            st.download_button(label="📥 Download Attendance Sheets (.xlsx)", data=buf.getvalue(), file_name="JK_Suzuki_Attendance.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        with st.expander("🖨 Showroom Official QR Code"):
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={SHOWROOM_QR_SECRET}", width=300)
            
        st.markdown("---")
        st.subheader("📋 Overall Attendance Data")
        st.dataframe(df_att, use_container_width=True)
