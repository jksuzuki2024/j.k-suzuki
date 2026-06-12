import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
        "admin": {"Name": "Showroom Owner", "Password": "admin786", "Role": "Admin", "Base_Salary": 0.0, "Shift_Time": "09:00 AM", "Joining_Date": "2026-01-01", "PIN": ""},
        "101": {"Name": "Amit Kumar", "Password": "password101", "Role": "Employee", "Base_Salary": 15000.0, "Shift_Time": "09:00 AM", "Joining_Date": "2026-01-01", "PIN": ""},
        "102": {"Name": "Rahul Singh", "Password": "password102", "Role": "Employee", "Base_Salary": 12000.0, "Shift_Time": "09:30 AM", "Joining_Date": "2026-01-05", "PIN": ""},
        "114": {"Name": "Jahir", "Password": "jahir", "Role": "Employee", "Base_Salary": 12000.0, "Shift_Time": "10:00 AM", "Joining_Date": "2026-01-10", "PIN": ""}
    }
    if not os.path.exists(DB_FILE):
        rows = [{"ID": str(k), "Name": v["Name"], "Password": str(v["Password"]), "Role": v["Role"], "Base_Salary": float(v["Base_Salary"]), "Shift_Time": v["Shift_Time"], "Joining_Date": v["Joining_Date"], "PIN": v["PIN"]} for k, v in fixed_accounts.items()]
        pd.DataFrame(rows).to_excel(DB_FILE, index=False)
    else:
        df = pd.read_excel(DB_FILE)
        if "Joining_Date" not in df.columns:
            df["Joining_Date"] = "2026-01-01"
        if "PIN" not in df.columns:
            df["PIN"] = ""
        df["PIN"] = df["PIN"].fillna("").astype(str)
        df.to_excel(DB_FILE, index=False)
    
    if not os.path.exists(ATT_FILE):
        pd.DataFrame(columns=["Date", "ID", "Name", "Entry Time", "Exit Time", "Status", "Is_Late"]).to_excel(ATT_FILE, index=False)

init_databases()

# Helper functions
def get_all_users():
    df = pd.read_excel(DB_FILE)
    if "Shift_Time" not in df.columns:
        df["Shift_Time"] = "09:00 AM"
    if "Joining_Date" not in df.columns:
        df["Joining_Date"] = "2026-01-01"
    if "PIN" not in df.columns:
        df["PIN"] = ""
    df["PIN"] = df["PIN"].fillna("").astype(str)
    return {
        str(row["ID"]).strip(): {
            "Name": row["Name"], 
            "Password": str(row["Password"]).strip(), 
            "Role": row["Role"], 
            "Base_Salary": float(row["Base_Salary"]), 
            "Shift_Time": str(row["Shift_Time"]),
            "Joining_Date": str(row["Joining_Date"]),
            "PIN": str(row["PIN"]).strip()
        } for _, row in df.iterrows()
    }

def add_user_to_db(uid, name, password, base_salary, shift_time, joining_date):
    df = pd.read_excel(DB_FILE)
    new_row = pd.DataFrame([{
        "ID": str(uid).strip(), 
        "Name": name, 
        "Password": str(password).strip(), 
        "Role": "Employee", 
        "Base_Salary": float(base_salary), 
        "Shift_Time": shift_time,
        "Joining_Date": str(joining_date),
        "PIN": ""
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(DB_FILE, index=False)

def update_user_pin(uid, new_pin):
    df = pd.read_excel(DB_FILE)
    df["ID"] = df["ID"].astype(str).str.strip()
    df.loc[df["ID"] == str(uid).strip(), "PIN"] = str(new_pin).strip()
    df.to_excel(DB_FILE, index=False)

def delete_user_from_db(emp_id):
    df_db = pd.read_excel(DB_FILE)
    df_db_filtered = df_db[df_db["ID"].astype(str) != str(emp_id)]
    df_db_filtered.to_excel(DB_FILE, index=False)
    
    df_att = pd.read_excel(ATT_FILE)
    df_att_filtered = df_att[df_att["ID"].astype(str) != str(emp_id)]
    df_att_filtered.to_excel(ATT_FILE, index=False)

def get_attendance():
    df = pd.read_excel(ATT_FILE)
    if "Is_Late" not in df.columns:
        df["Is_Late"] = "No"
    if "Status" not in df.columns:
        df["Status"] = "Present"
    return df

def save_attendance(df):
    df.to_excel(ATT_FILE, index=False)

def clear_employee_attendance(emp_id):
    df_att = get_attendance()
    df_filtered = df_att[df_att["ID"].astype(str) != str(emp_id)]
    save_attendance(df_filtered)

def check_if_late(entry_str, shift_str):
    try:
        t_entry = datetime.strptime(entry_str, "%I:%M %p").time()
        t_shift = datetime.strptime(shift_str, "%I:%M %p").time()
        return "Yes" if t_entry > t_shift else "No"
    except:
        return "No"

def calculate_salary_report(emp_id, base_salary, joining_date_str):
    total_cycle_days = 30
    allowed_holidays = 4
    df_att = get_attendance()
    
    try:
        j_date = datetime.strptime(joining_date_str, "%Y-%m-%d").date()
    except:
        j_date = datetime.now(KOLKATA_TZ).date()
        
    current_today = datetime.now(KOLKATA_TZ).date()
    
    if current_today >= j_date:
        elapsed_days = (current_today - j_date).days + 1
        elapsed_days = min(elapsed_days, total_cycle_days)
    else:
        elapsed_days = 1
        
    full_present_days = 0
    half_days = 0
    late_days = 0
    
    if not df_att.empty:
        emp_logs = df_att[df_att["ID"].astype(str) == str(emp_id)]
        full_present_days = len(emp_logs[emp_logs["Status"] == "Present"])
        half_days = len(emp_logs[emp_logs["Status"] == "Half Day"])
        late_days = len(emp_logs[emp_logs["Is_Late"] == "Yes"])
        
    total_present_credit = full_present_days + (half_days * 0.5)
    actual_absents = max(0.0, elapsed_days - (full_present_days + half_days))
    
    paid_days = min(total_present_credit + allowed_holidays, total_cycle_days)
    final_unpaid_absents = max(0.0, total_cycle_days - paid_days)
    
    per_day_salary = base_salary / total_cycle_days
    
    late_fine_days = 0.0
    if late_days >= 10:
        late_fine_days = 1.0
    elif late_days >= 5:
        late_fine_days = 0.5
        
    net_payable = round((paid_days - late_fine_days) * per_day_salary, 2)
    net_payable = max(0.0, net_payable)
    
    total_deduction = round((final_unpaid_absents + late_fine_days) * per_day_salary, 2)
    
    return full_present_days, half_days, allowed_holidays, actual_absents, late_days, net_payable, total_deduction

def get_next_salary_date(joining_date_str):
    try:
        j_date = datetime.strptime(joining_date_str, "%Y-%m-%d")
        next_date = j_date + timedelta(days=30)
        return next_date.strftime("%d %b, %Y")
    except:
        return "Not Set"

# App Configuration
st.set_page_config(page_title="JK Motors Pro System", layout="wide")
st.title("🏍️ JK Motors Attendance, Shift & Salary Portal")
st.markdown("---")

# Persistent Session Management
if 'logged_in_uid' not in st.session_state:
    st.session_state.logged_in_uid = ""
if 'is_pin_unlocked' not in st.session_state:
    st.session_state.is_pin_unlocked = False

all_users = get_all_users()

# --- 1. USER IS LOGGED IN ---
if st.session_state.logged_in_uid != "":
    current_uid = st.session_state.logged_in_uid
    user_info = all_users.get(current_uid)
    
    if not user_info:
        st.session_state.logged_in_uid = ""
        st.session_state.is_pin_unlocked = False
        st.rerun()
        
    # Security PIN Lock Check (For Employees who have set a PIN)
    if user_info["Role"] == "Employee" and user_info["PIN"] != "" and not st.session_state.is_pin_unlocked:
        st.subheader(f"🔒 Profile Locked: {user_info['Name']}")
        st.info("আপনার প্রোফাইলটি আনলক করতে আপনার ৪ ডিজিটের পিন নম্বরটি দিন।")
        
        entered_pin = st.text_input("Enter Profile PIN:", type="password", max_chars=4, key="profile_pin_lock_input").strip()
        
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("Unlock Profile", type="primary", key="unlock_profile_action"):
                if entered_pin == user_info["PIN"]:
                    st.session_state.is_pin_unlocked = True
                    st.success("Access Granted!")
                    st.rerun()
                else:
                    st.error("❌ ভুল পিন!")
        with col_btn2:
            if st.button("Change Account / Full Logout", key="full_logout_from_pin_screen"):
                st.session_state.logged_in_uid = ""
                st.session_state.is_pin_unlocked = False
                st.rerun()
        st.stop()

    # Sidebar Profile Info
    st.sidebar.subheader(f"👤 {user_info['Name']}")
    st.sidebar.write(f"**ID:** {current_uid} | **Role:** {user_info['Role']}")
    
    if user_info['Role'] == "Employee":
        st.sidebar.write(f"⏰ **Shift Time:** {user_info['Shift_Time']}")
        st.sidebar.write(f"📅 **Joining Date:** {user_info['Joining_Date']}")
        
        # PIN Configuration Section inside Employee Sidebar
        with st.sidebar.expander("🔐 Set/Change Your Profile PIN"):
            if user_info["PIN"] == "":
                st.warning("আপনি এখনো কোনো পিন সেট করেননি।")
                new_pin = st.text_input("Create 4-Digit PIN:", type="password", max_chars=4, key="create_new_pin_widget").strip()
                if st.button("Save PIN", key="save_new_pin_btn"):
                    if len(new_pin) == 4 and new_pin.isdigit():
                        update_user_pin(current_uid, new_pin)
                        st.session_state.is_pin_unlocked = True
                        st.success("✅ পিন সেট হয়েছে! এরপর থেকে পিন দিয়ে প্রোফাইল খুলবে।")
                        st.rerun()
                    else:
                        st.error("পিন অবশ্যই ৪টি সংখ্যার হতে হবে!")
            else:
                st.success("🔒 পিন লক সক্রিয় আছে।")
                change_pin = st.text_input("Enter New PIN:", type="password", max_chars=4, key="change_existing_pin_widget").strip()
                if st.button("Update PIN", key="update_existing_pin_btn"):
                    if len(change_pin) == 4 and change_pin.isdigit():
                        update_user_pin(current_uid, change_pin)
                        st.session_state.is_pin_unlocked = True
                        st.success("✅ পিন সফলভাবে পরিবর্তন হয়েছে!")
                        st.rerun()
                    else:
                        st.error("পিন অবশ্যই ৪টি সংখ্যার হতে হবে!")

    if st.sidebar.button("Full Logout (আইডি-পাসওয়ার্ড মুছুন)", type="secondary", key="sidebar_logout_button"):
        st.session_state.logged_in_uid = ""
        st.session_state.is_pin_unlocked = False
        st.rerun()

    # --- EMPLOYEE INTERFACE ---
    if user_info["Role"] == "Employee":
        f_days, h_days, hol_days, a_days, l_days, p_sal, ded = calculate_salary_report(current_uid, user_info['Base_Salary'], user_info['Joining_Date'])
        next_pay_day = get_next_salary_date(user_info['Joining_Date'])
        
        st.subheader("📊 Your Live Attendance & Leave Deduction Sheet")
        st.warning(f"🗓️ **Your Joining Date:** {user_info['Joining_Date']} | 🗓️ **Next Salary Calculation Cycle:** {next_pay_day}")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric(label="🟢 Full Present Days", value=f"{f_days} Days")
        with c2: st.metric(label="🟡 Half Days Worked", value=f"{h_days} Days")
        with c3: st.metric(label="❌ Actual Absents", value=f"{a_days} Days")
        with c4: st.metric(label="📉 Total Salary Deducted", value=f"₹{ded}")
            
        st.info(f"⚠️ **Note:** আপনার লেট হাজিরার সংখ্যা: **{l_days} দিন**। প্রতি মাসে ৪টি পেইড লিভ (Paid Leave) সিস্টেমে অটোমেটিক যোগ করা থাকে।")
        
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
            val = qrcode_scanner(key='entry_scanner_active_view')
            if val == SHOWROOM_QR_SECRET:
                is_late_status = check_if_late(c_time, user_info['Shift_Time'])
                attendance_status = "Present"
                if now_k.hour >= 14:
                    attendance_status = "Half Day"
                
                new_row = pd.DataFrame([{"Date": c_date, "ID": str(current_uid), "Name": user_info['Name'], "Entry Time": c_time, "Exit Time": "Not Out Yet", "Status": attendance_status, "Is_Late": is_late_status}])
                save_attendance(pd.concat([df_att, new_row], ignore_index=True))
                st.success(f"✅ ENTRY Recorded! Status: {attendance_status}")
                st.rerun()
        elif today_entry.iloc[0]["Exit Time"] == "Not Out Yet":
            st.info("⚠️ ছুটির সময় বিদায় নেওয়ার জন্য আবার QR Code স্ক্যান করুন।")
            val = qrcode_scanner(key='exit_scanner_active_view')
            if val == SHOWROOM_QR_SECRET:
                if now_k.hour < 14:
                    df_att.loc[(df_att["Date"] == c_date) & (df_att["ID"].astype(str) == str(current_uid)), "Status"] = "Half Day"
                
                df_att.loc[(df_att["Date"] == c_date) & (df_att["ID"].astype(str) == str(current_uid)), "Exit Time"] = c_time
                save_attendance(df_att)
                st.success("✅ EXIT Recorded!")
                st.rerun()
        else:
            st.success("🎉 Today's Attendance Completed!")
            
        st.markdown("---")
        st.subheader("📋 Your Attendance History Logs")
        st.dataframe(df_att[df_att["ID"].astype(str) == str(current_uid)], use_container_width=True)

    # --- OWNER / ADMIN CONTROL PANEL ---
    elif user_info["Role"] == "Admin":
        st.subheader("👑 Owner Control Panel")
        
        with st.expander("➕ Add New Employee & Shift Time"):
            n_id = st.text_input("New Employee ID No:", key="owner_create_uid").strip()
            n_name = st.text_input("Employee Full Name:", key="owner_create_name").strip()
            n_pass = st.text_input("Set Password:", key="owner_create_pass").strip()
            n_sal = st.number_input("Monthly Base Salary (₹):", min_value=0, value=12000, key="owner_create_sal")
            n_jdate = st.date_input("Select Employee Joining Date:", value=datetime.now(KOLKATA_TZ).date(), key="owner_create_jdate")
            
            shift_h = st.selectbox("Shift Hour:", [f"{i:02d}" for i in range(1, 13)], index=8, key="owner_create_sh")
            shift_m = st.selectbox("Shift Minute:", [f"{i:02d}" for i in range(0, 60, 5)], index=0, key="owner_create_sm")
            shift_p = st.selectbox("AM/PM:", ["AM", "PM"], index=0, key="owner_create_sp")
            final_shift_time = f"{shift_h}:{shift_m} {shift_p}"
            
            if st.button("Create Permanent Account", type="primary", key="owner_create_submit_btn"):
                if n_id in all_users:
                    st.error("❌ ID already exists!")
                elif n_id == "" or n_name == "" or n_pass == "":
                    st.error("❌ Fill all fields!")
                else:
                    add_user_to_db(n_id, n_name, n_pass, n_sal, final_shift_time, str(n_jdate))
                    st.success(f"✅ Employee {n_name} added successfully!")
                    st.rerun()
                    
        st.markdown("---")
        
        # Gather data for report
        report_rows = []
        for uid, udata in all_users.items():
            if udata["Role"] == "Employee":
                f_days, h_days, hol_days, a_days, l_days, p_sal, ded = calculate_salary_report(uid, udata['Base_Salary'], udata.get('Joining_Date', '2026-01-01'))
                next_pay = get_next_salary_date(udata.get('Joining_Date', '2026-01-01'))
                report_rows.append({
                    "ID": uid, "Name": udata["Name"], "Joining Date": udata.get('Joining_Date', '2026-01-01'),
                    "Salary Due Date": next_pay, "Target Time": udata["Shift_Time"], "Base Salary (₹)": udata["Base_Salary"],
                    "Full Day": f_days, "Half Day": h_days, "Late Days": l_days, "Net Payable Salary (₹)": p_sal, "Actual Absents": a_days
                })
        df_report = pd.DataFrame(report_rows)
        
        # 🔎 Live Search Employee Bar
        st.subheader("🔎 Search Employee Profile")
        search_query = st.text_input("Enter Employee ID or Name to Filter:", placeholder="e.g. 114 or Jahir", key="admin_live_search_box").strip().lower()
        
        if search_query and not df_report.empty:
            filtered_df = df_report[df_report["ID"].str.lower().str.contains(search_query) | df_report["Name"].str.lower().str.contains(search_query)]
            if not filtered_df.empty:
                st.info(f"🎯 Search Results ({len(filtered_df)} Found):")
                for _, row in filtered_df.iterrows():
                    emp_id_str = str(row["ID"])
                    st.write(f"📅 **Join Date:** {row['Joining Date']} | 🗓️ **Next Salary Calculation Cycle:** {row['Salary Due Date']}")
                    cs1, cs2, cs3, cs4, cs5, cs6, cs7 = st.columns([1, 1.8, 1.1, 1.1, 1.1, 1.2, 1.4])
                    cs1.write(f"**ID:** {emp_id_str}")
                    cs2.write(f"**Name:** {row['Name']}")
                    cs3.write(f"🟢 Full: **{row['Full Day']}**")
                    cs4.write(f"🟡 Half: **{row['Half Day']}**")
                    cs5.write(f"❌ Abs: **{row['Actual Absents']}**")
                    cs6.write(f"⚠️ Late: **{row['Late Days']}**")
                    cs7.write(f"💰 Pay: **₹{row['Net Payable Salary (₹)']}**")
                    
                    cb1, cb2 = st.columns(2)
                    with cb1:
                        if st.button("🔄 Paid & Refresh", key=f"search_view_pay_refresh_{emp_id_str}"):
                            clear_employee_attendance(emp_id_str)
                            st.success("Attendance Reset Successfully!")
                            st.rerun()
                    with cb2:
                        if st.button("🗑️ Delete Account", key=f"search_view_delete_account_{emp_id_str}"):
                            delete_user_from_db(emp_id_str)
                            st.warning("Employee Record Deleted!")
                            st.rerun()
                    st.markdown("---")
            else:
                st.error("❌ No Employee found with this ID or Name.")
        
        st.markdown("---")
        
        # 📊 Overall Master Live Salary Sheet Panel
        st.subheader("📊 Employees Monthly Live Salary Sheet (Admin Overview)")
        if not df_report.empty:
            for _, row in df_report.iterrows():
                emp_id_str = str(row["ID"])
                st.write(f"📅 **Join Date:** {row['Joining Date']} | 🗓️ **Next Salary Calculation Cycle:** {row['Salary Due Date']}")
                col_emp1, col_emp2, col_emp3, col_emp4, col_emp5, col_emp6, col_emp7 = st.columns([1, 1.8, 1.1, 1.1, 1.1, 1.2, 1.4])
                col_emp1.write(f"**ID:** {emp_id_str}")
                col_emp2.write(f"**Name:** {row['Name']}")
                col_emp3.write(f"🟢 Full: **{row['Full Day']}**")
                col_emp4.write(f"🟡 Half: **{row['Half Day']}**")
                col_emp5.write(f"❌ Abs: **{row['Actual Absents']}**")
                col_emp6.write(f"⚠️ Late: **{row['Late Days']}**")
                col_emp7.write(f"💰 Pay: **₹{row['Net Payable Salary (₹)']}**")
                
                col_mbtn1, col_mbtn2 = st.columns(2)
                with col_mbtn1:
                    if st.button("🔄 Paid & Refresh", key=f"master_view_pay_refresh_{emp_id_str}"):
                        clear_employee_attendance(emp_id_str)
                        st.success("Attendance Reset Done!")
                        st.rerun()
