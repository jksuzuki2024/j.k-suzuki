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
        "admin": {"Name": "Showroom Owner", "Password": "admin786", "Role": "Admin", "Base_Salary": 0, "Shift_Time": "09:00 AM"},
        "101": {"Name": "Amit Kumar", "Password": "password101", "Role": "Employee", "Base_Salary": 15000, "Shift_Time": "09:00 AM"},
        "102": {"Name": "Rahul Singh", "Password": "password102", "Role": "Employee", "Base_Salary": 12000, "Shift_Time": "09:30 AM"},
        "114": {"Name": "Jahir", "Password": "jahir", "Role": "Employee", "Base_Salary": 12000, "Shift_Time": "10:00 AM"}
    }
    if not os.path.exists(DB_FILE):
        rows = [{"ID": str(k), "Name": v["Name"], "Password": str(v["Password"]), "Role": v["Role"], "Base_Salary": float(v["Base_Salary"]), "Shift_Time": v["Shift_Time"]} for k, v in fixed_accounts.items()]
        pd.DataFrame(rows).to_excel(DB_FILE, index=False)
    
    if not os.path.exists(ATT_FILE):
        pd.DataFrame(columns=["Date", "ID", "Name", "Entry Time", "Exit Time", "Status", "Is_Late"]).to_excel(ATT_FILE, index=False)

init_databases()

# Helper functions
def get_all_users():
    df = pd.read_excel(DB_FILE)
    if "Shift_Time" not in df.columns:
        df["Shift_Time"] = "09:00 AM"
    return {str(row["ID"]).strip(): {"Name": row["Name"], "Password": str(row["Password"]).strip(), "Role": row["Role"], "Base_Salary": float(row["Base_Salary"]), "Shift_Time": str(row["Shift_Time"])} for _, row in df.iterrows()}

def add_user_to_db(uid, name, password, base_salary, shift_time):
    df = pd.read_excel(DB_FILE)
    new_row = pd.DataFrame([{"ID": str(uid).strip(), "Name": name, "Password": str(password).strip(), "Role": "Employee", "Base_Salary": float(base_salary), "Shift_Time": shift_time}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(DB_FILE, index=False)

def get_attendance():
    df = pd.read_excel(ATT_FILE)
    if "Is_Late" not in df.columns:
        df["Is_Late"] = "No"
    return df

def save_attendance(df):
    df.to_excel(ATT_FILE, index=False)

# Refresh logic to clear attendance for a specific employee
def clear_employee_attendance(emp_id):
    df_att = get_attendance()
    df_filtered = df_att[df_att["ID"].astype(str) != str(emp_id)]
    save_attendance(df_filtered)

# Time checker logic for Late count
def check_if_late(entry_str, shift_str):
    try:
        t_entry = datetime.strptime(entry_str, "%I:%M %p").time()
        t_shift = datetime.strptime(shift_str, "%I:%M %p").time()
        return "Yes" if t_entry > t_shift else "No"
    except:
        return "No"

# Salary & Fine Logic
def calculate_salary_report(emp_id, base_salary):
    total_days = 30
    allowed_holidays = 4
    df_att = get_attendance()
    
    if not df_att.empty:
        emp_logs = df_att[df_att["ID"].astype(str) == str(emp_id)]
        present_days = emp_logs["Date"].nunique()
        late_days = len(emp_logs[emp_logs["Is_Late"] == "Yes"])
    else:
        present_days = 0
        late_days = 0
        
    paid_days = min(present_days + allowed_holidays, total_days)
    absent_days = max(0, total_days - paid_days)
    
    per_day_salary = base_salary / total_days
    
    late_fine_days = 0.0
    if late_days >= 10:
        late_fine_days = 1.0
    elif late_days >= 5:
        late_fine_days = 0.5
        
    net_payable = round((paid_days - late_fine_days) * per_day_salary, 2)
    net_payable = max(0.0, net_payable)
    
    total_deduction = round((absent_days + late_fine_days) * per_day_salary, 2)
    late_penalty_cost = round(late_fine_days * per_day_salary, 2)
    
    return present_days, allowed_holidays, absent_days, late_days, late_penalty_cost, net_payable, total_deduction

# App Config
st.set_page_config(page_title="JK Suzuki Pro System", layout="wide")
st.title("🏍️ JK Suzuki Attendance, Shift & Salary Portal")
st.markdown("---")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = ""

all_users = get_all_users()

# FIXED: Login section logic separated completely to prevent UI breaking
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
    if user_info['Role'] == "Employee":
        st.sidebar.write(f"⏰ **Your Shift Time:** {user_info['Shift_Time']}")
        
    if st.sidebar.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.rerun()
        
    # EMPLOYEE VIEW
    if user_info["Role"] == "Employee":
        p_days, h_days, a_days, l_days, l_fine, p_sal, ded = calculate_salary_report(current_uid, user_info['Base_Salary'])
        
        st.subheader("📊 Your Live Salary & Attendance Sheet")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(label="Base Salary", value=f"₹{user_info['Base_Salary']}")
            st.write(f"💼 **Days Present:** {p_days}")
        with c2:
            st.metric(label="Net Payable Salary", value=f"₹{p_sal}")
            st.write(f"🌴 **Paid Leaves:** {h_days} Days")
        with c3:
            st.metric(label="Late Fine Deducted", value=f"₹{l_fine}")
            st.write(f"⚠️ **Total Late Days:** {l_days} Days")
        with c4:
            st.metric(label="Total Deducted (Absent+Late)", value=f"₹{ded}")
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
            st.warning("📋 আপনার আজকের হাজিরা দেওয়া হয়নি। শোরুমের QR Code স্ক্যান করুন।")
            val = qrcode_scanner(key='entry_scan')
            if val == SHOWROOM_QR_SECRET:
                is_late_status = check_if_late(c_time, user_info['Shift_Time'])
                new_row = pd.DataFrame([{"Date": c_date, "ID": str(current_uid), "Name": user_info['Name'], "Entry Time": c_time, "Exit Time": "Not Out Yet", "Status": "Present", "Is_Late": is_late_status}])
                save_attendance(pd.concat([df_att, new_row], ignore_index=True))
                st.success(f"✅ ENTRY Recorded! Late Status: {is_late_status}")
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

    # ADMIN VIEW
    elif user_info["Role"] == "Admin":
        st.subheader("👑 Owner Control Panel")
        
        with st.expander("➕ Add New Employee & Shift Time (নতুন কর্মচারী ও টাইম সেট করুন)"):
            n_id = st.text_input("New Employee ID No:").strip()
            n_name = st.text_input("Employee Full Name:").strip()
            n_pass = st.text_input("Set Password:").strip()
            n_sal = st.number_input("Monthly Base Salary (₹):", min_value=0, value=12000)
            
            shift_h = st.selectbox("Shift Hour:", [f"{i:02d}" for i in range(1, 13)], index=8)
            shift_m = st.selectbox("Shift Minute:", [f"{i:02d}" for i in range(0, 60, 5)], index=0)
            shift_p = st.selectbox("AM/PM:", ["AM", "PM"], index=0)
            final_shift_time = f"{shift_h}:{shift_m} {shift_p}"
            st.write(f"Selected Entry Cutoff: **{final_shift_time}**")
            
            if st.button("Create Permanent Account", type="primary"):
                if n_id in all_users:
                    st.error("❌ ID already exists!")
                elif n_id=="" or n_name=="" or n_pass=="":
                    st.error("❌ Fill all fields!")
                else:
                    add_user_to_db(n_id, n_name, n_pass, n_sal, final_shift_time)
                    st.success(f"✅ Employee {n_name} added permanently!")
                    st.rerun()
                    
        st.markdown("---")
        
        # Gathering all data rows for report
        report_rows = []
        for uid, udata in all_users.items():
            if udata["Role"] == "Employee":
                p_days, h_days, a_days, l_days, l_fine, p_sal, ded = calculate_salary_report(uid, udata['Base_Salary'])
                report_rows.append({
                    "ID": uid,
                    "Name": udata["Name"],
                    "Target Time": udata["Shift_Time"],
                    "Base Salary (₹)": udata["Base_Salary"],
                    "Present Days": p_days,
                    "Late Days": l_days,
                    "Late Fine (₹)": l_fine,
                    "Net Payable Salary (₹)": p_sal,
                    "Total Deductions (₹)": ded
                })
        
        df_report = pd.DataFrame(report_rows)
        
        # 🔎 SEARCH EMPLOYEE SECTION
        st.subheader("🔎 Search Employee Profile (আইডি বা নাম দিয়ে খুঁজুন)")
        search_query = st.text_input("Enter Employee ID or Name to Search:", placeholder="e.g. 114 or Jahir").strip().lower()
        
        if search_query and not df_report.empty:
            filtered_df = df_report[df_report["ID"].str.lower().str.contains(search_query) | df_report["Name"].str.lower().str.contains(search_query)]
            
            if not filtered_df.empty:
                st.info(f"🎯 Found {len(filtered_df)} result(s):")
                for _, row in filtered_df.iterrows():
                    emp_id_str = str(row["ID"])
                    with st.container():
                        c_s1, c_s2, c_s3, c_s4, c_s5, c_s6, c_s7 = st.columns([1, 2, 1.5, 1.5, 1.5, 1.5, 2])
                        with c_s1:
                            st.write(f"**ID:** {emp_id_str}")
                        with c_s2:
                            st.write(f"**Name:** {row['Name']}")
                        with c_s3:
                            st.write(f"💼 Present: **{row['Present Days']}**")
                        with c_s4:
                            st.write(f"⚠️ Late: **{row['Late Days']}**")
                        with c_s5:
                            st.write(f"📉 Fine: **₹{row['Late Fine (₹)']}**")
                        with c_s6:
                            st.write(f"💰 Net Pay: **₹{row['Net Payable Salary (₹)']}**")
                        with c_s7:
                            if st.button(f"🔄 Paid & Refresh", key=f"src_ref_{emp_id_str}", type="primary"):
                                clear_employee_attendance(emp_id_str)
                                st.success(f"Reset done for {row['Name']}!")
                                st.rerun()
                    st.markdown("<hr style='margin:0.5em 0px; border-color:#ff4b4b;'>", unsafe_allow_html=True)
            else:
                st.error("❌ No Employee found with that ID or Name!")
        
        st.markdown("---")
        
        # OVERVIEW TABLE SHOWING ALL ACCOUNTS
        st.subheader("📊 Employees Master Live Salary Sheet (All Overview)")
        if not df_report.empty:
            for _, row in df_report.iterrows():
                emp_id_str = str(row["ID"])
                with st.container():
                    col_emp1, col_emp2, col_emp3, col_emp4, col_emp5, col_emp6, col_emp7 = st.columns([1, 2, 1.5, 1.5, 1.5, 1.5, 2])
                    with col_emp1:
                        st.write(f"**ID:** {emp_id_str}")
                    with col_emp2:
                        st.write(f"**Name:** {row['Name']}")
                    with col_emp3:
                        st.write(f"💼 Present: **{row['Present Days']}**")
                    with col_emp4:
                        st.write(f"⚠️ Late: **{row['Late Days']}**")
                    with col_emp5:
                        st.write(f"📉 Fine: **₹{row['Late Fine (₹)']}**")
                    with col_emp6:
                        st.write(f"💰 Net Pay: **₹{row['Net Payable Salary (₹)']}**")
                    with col_emp7:
                        if st.button(f"🔄 Paid & Refresh", key=f"main_ref_{emp_id_str}", type="secondary"):
                            clear_employee_attendance(emp_id_str)
                            st.success(f"Reset done for {row['Name']}!")
                            st.rerun()
                st.markdown("<hr style='margin:0.5em 0px;'>", unsafe_allow_html=True)
        else:
            st.info("No employee accounts registered yet.")

        st.markdown("---")
        df_att = get_attendance()
        if not df_att.empty:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                df_att.to_excel(writer, index=False, sheet_name='Sheet1')
            st.download_button(label="📥 Download Master Attendance Sheets (.xlsx)", data=buf.getvalue(), file_name="JK_Suzuki_Master_Attendance.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        with st.expander("🖨 Showroom Official QR Code"):
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={SHOWROOM_QR_SECRET}", width=300)
            
        st.markdown("---")
        st.subheader("📋 Overall Master Attendance Logs (All Database)")
        st.dataframe(df_att, use_container_width=True)
