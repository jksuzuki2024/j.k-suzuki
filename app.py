import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import pytz
import io

# Timezone Configuration
KOLKATA_TZ = pytz.timezone("Asia/Kolkata")
SHOWROOM_QR_SECRET = "JK_SUZUKI_SHOWROOM_OFFICIAL_ATTENDANCE_2026"

DB_FILE = "employee_database.xlsx"
ATT_FILE = "attendance_database.xlsx"

def init_databases():
    fixed_accounts = {
        "admin": {"Name": "Showroom Owner", "Password": "admin786", "Role": "Admin", "Base_Salary": 0.0, "Shift_Time": "09:00 AM", "Joining_Date": "2026-01-01", "PIN": ""},
        "101": {"Name": "Amit Kumar", "Password": "password101", "Role": "Employee", "Base_Salary": 15000.0, "Shift_Time": "09:00 AM", "Joining_Date": "2026-01-01", "PIN": ""},
        "102": {"Name": "Rahul Singh", "Password": "password102", "Role": "Employee", "Base_Salary": 12000.0, "Shift_Time": "09:30 AM", "Joining_Date": "2026-01-05", "PIN": ""},
        "114": {"Name": "Jahir", "Password": "jahir", "Role": "Employee", "Base_Salary": 12000.0, "Shift_Time": "10:00 AM", "Joining_Date": "2026-01-10", "PIN": ""}
    }
    if not os.path.exists(DB_FILE):
        rows = []
        for k, v in fixed_accounts.items():
            rows.append({
                "ID": str(k), "Name": v["Name"], "Password": str(v["Password"]), 
                "Role": v["Role"], "Base_Salary": float(v["Base_Salary"]), 
                "Shift_Time": v["Shift_Time"], "Joining_Date": v["Joining_Date"], "PIN": v["PIN"]
            })
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

def get_all_users():
    df = pd.read_excel(DB_FILE)
    if "Shift_Time" not in df.columns:
        df["Shift_Time"] = "09:00 AM"
    if "Joining_Date" not in df.columns:
        df["Joining_Date"] = "2026-01-01"
    if "PIN" not in df.columns:
        df["PIN"] = ""
    df["PIN"] = df["PIN"].fillna("").astype(str)
    
    users = {}
    for _, row in df.iterrows():
        uid = str(row["ID"]).strip()
        users[uid] = {
            "Name": row["Name"], 
            "Password": str(row["Password"]).strip(), 
            "Role": row["Role"], 
            "Base_Salary": float(row["Base_Salary"]), 
            "Shift_Time": str(row["Shift_Time"]),
            "Joining_Date": str(row["Joining_Date"]),
            "PIN": str(row["PIN"]).strip()
        }
    return users

def add_user_to_db(uid, name, password, base_salary, shift_time, joining_date):
    df = pd.read_excel(DB_FILE)
    new_row = pd.DataFrame([{
        "ID": str(uid).strip(), "Name": name, "Password": str(password).strip(), 
        "Role": "Employee", "Base_Salary": float(base_salary), 
        "Shift_Time": shift_time, "Joining_Date": str(joining_date), "PIN": ""
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
    df_db = df_db[df_db["ID"].astype(str) != str(emp_id)]
    df_db.to_excel(DB_FILE, index=False)
    
    df_att = pd.read_excel(ATT_FILE)
    df_att = df_att[df_att["ID"].astype(str) != str(emp_id)]
    df_att.to_excel(ATT_FILE, index=False)

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
        if t_entry > t_shift:
            return "Yes"
        return "No"
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

# Streamlit Page Setting
st.set_page_config(page_title="JK Motors Pro System", layout="wide")
st.title("🏍️ JK Motors Attendance, Shift & Salary Portal")
st.markdown("---")

if 'logged_in_uid' not in st.session_state:
    st.session_state.logged_in_uid = ""
if 'is_pin_unlocked' not in st.session_state:
    st.session_state.is_pin_unlocked = False

all_users = get_all_users()

# --- 1. SESSION MANAGEMENT: USER LOGGED IN ---
if st.session_state.logged_in_uid != "":
    current_uid = st.session_state.logged_in_uid
    user_info = all_users.get(current_uid)
    
    if not user_info:
        st.session_state.logged_in_uid = ""
        st.session_state.is_pin_unlocked = False
        st.rerun()
        
    # Security PIN Lock Verification Screen
    if user_info["Role"] == "Employee" and user_info["PIN"] != "" and not st.session_state.is_pin_unlocked:
        st.subheader(f"🔒 Profile Locked: {user_info['Name']}")
        st.info("আপনার ৪ ডিজিটের পিন নম্বরটি দিয়ে প্রোফাইল আনলক করুন।")
        
        entered_pin = st.text_input("Enter PIN:", type="password", max_chars=4, key="profile_pin_lock_input").strip()
        
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("Unlock Profile", type="primary"):
                if entered_pin == user_info["PIN"]:
                    st.session_state.is_pin_unlocked = True
                    st.success("Access Granted!")
                    st.rerun()
                else:
                    st.error("❌ ভুল পিন নম্বর!")
        with col_btn2:
            if st.button("Logout Account", key="logout_pin_scr"):
                st.session_state.logged_in_uid = ""
                st.session_state.is_pin_unlocked = False
                st.rerun()
        st.stop()

    # Sidebar Panel
    st.sidebar.subheader(f"👤 {user_info['Name']}")
    st.sidebar.write(f"ID: {current_uid} | Role: {user_info['Role']}")
    
    if user_info['Role'] == "Employee":
        st.sidebar.write(f"Shift Time: {user_info['Shift_Time']}")
        st.sidebar.write(f"Joining Date: {user_info['Joining_Date']}")
        
        with st.sidebar.expander("🔐 Set/Change Profile PIN"):
            if user_info["PIN"] == "":
                st.warning("পিন সেট করা নেই।")
                new_pin = st.text_input("Create 4-Digit PIN:", type="password", max_chars=4, key="c_pin").strip()
                if st.button("Save PIN", key="s_pin_btn"):
                    if len(new_pin) == 4 and new_pin.isdigit():
                        update_user_pin(current_uid, new_pin)
                        st.session_state.is_pin_unlocked = True
                        st.success("✅ পিন সেট হয়েছে!")
                        st.rerun()
                    else:
                        st.error("পিন অবশ্যই ৪ ডিজিটের সংখ্যা হবে!")
            else:
                st.success("🔒 পিন লক সক্রিয় রয়েছে।")
                change_pin = st.text_input("Enter New PIN:", type="password", max_chars=4, key="ch_pin").strip()
                if st.button("Update PIN", key="u_pin_btn"):
                    if len(change_pin) == 4 and change_pin.isdigit():
                        update_user_pin(current_uid, change_pin)
                        st.session_state.is_pin_unlocked = True
                        st.success("✅ পিন আপডেট হয়েছে!")
                        st.rerun()
                    else:
                        st.error("পিন অবশ্যই ৪ ডিজিটের সংখ্যা হবে!")

    if st.sidebar.button("Full Logout (Clear Session)", type="secondary"):
        st.session_state.logged_in_uid = ""
        st.session_state.is_pin_unlocked = False
        st.rerun()

    # --- EMPLOYEE VIEW ---
    if user_info["Role"] == "Employee":
        f_days, h_days, hol_days, a_days, l_days, p_sal, ded = calculate_salary_report(current_uid, user_info['Base_Salary'], user_info['Joining_Date'])
        next_pay_day = get_next_salary_date(user_info['Joining_Date'])
        
        st.subheader("📊 Attendance & Salary Sheet")
        st.warning(f"Joining Date: {user_info['Joining_Date']} | Next Cycle Due: {next_pay_day}")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric(label="🟢 Full Present", value=f"{f_days} Days")
        with c2: st.metric(label="🟡 Half Days", value=f"{h_days} Days")
        with c3: st.metric(label="❌ Total Absents", value=f"{a_days} Days")
        with c4: st.metric(label="📉 Total Deducted", value=f"Base: ₹{ded}")
            
        st.info(f"আপনার লেট হাজিরার সংখ্যা: {l_days} দিন। সিস্টেমে প্রতি মাসে ৪টি পেইড লিভ বরাদ্দ থাকে।")
        
        st.markdown("---")
        st.subheader("📷 Attendance Scanner")
        from streamlit_qrcode_scanner import qrcode_scanner
        now_k = datetime.now(KOLKATA_TZ)
        c_date = str(now_k.date())
        c_time = now_k.strftime("%I:%M %p")
        st.info(f"Current Date: {c_date} | Time: {c_time}")
        
        df_att = get_attendance()
        today_entry = df_att[(df_att["Date"] == c_date) & (df_att["ID"].astype(str) == str(current_uid))]
        
        if today_entry.empty:
            st.warning("📋 আজকের হাজিরা দেওয়া হয়নি। শোরুমের QR Code স্ক্যান করুন।")
            val = qrcode_scanner(key='entry_scan')
            if val == SHOWROOM_QR_SECRET:
                is_late_status = check_if_late(c_time, user_info['Shift_Time'])
                attendance_status = "Present"
                if now_k.hour >= 14:
                    attendance_status = "Half Day"
                
                new_row = pd.DataFrame([{"Date": c_date, "ID": str(current_uid), "Name": user_info['Name'], "Entry Time": c_time, "Exit Time": "Not Out Yet", "Status": attendance_status, "Is_Late": is_late_status}])
                save_attendance(pd.concat([df_att, new_row], ignore_index=True))
                st.success("✅ Entry Recorded!")
                st.rerun()
        elif today_entry.iloc[0]["Exit Time"] == "Not Out Yet":
            st.info("⚠️ ছুটির সময় বিদায় নিতে পুনরায় QR Code স্ক্যান করুন।")
            val = qrcode_scanner(key='exit_scan')
            if val == SHOWROOM_QR_SECRET:
                if now_k.hour < 14:
                    df_att.loc[(df_att["Date"] == c_date) & (df_att["ID"].astype(str) == str(current_uid)), "Status"] = "Half Day"
                
                df_att.loc[(df_att["Date"] == c_date) & (df_att["ID"].astype(str) == str(current_uid)), "Exit Time"] = c_time
                save_attendance(df_att)
                st.success("✅ Exit Recorded!")
                st.rerun()
        else:
            st.success("🎉 Today's Attendance Completed!")
            
        st.markdown("---")
        st.subheader("📋 Personal Log History")
        st.dataframe(df_att[df_att["ID"].astype(str) == str(current_uid)], use_container_width=True)

    # --- OWNER / ADMIN PANEL ---
    elif user_info["Role"] == "Admin":
        st.subheader("👑 Owner Management Panel")
        
        with st.expander("➕ Register New Employee & Shift"):
            n_id = st.text_input("Employee ID No:", key="adm_id").strip()
            n_name = st.text_input("Full Name:", key="adm_name").strip()
            n_pass = st.text_input("Password:", key="adm_pass").strip()
            n_sal = st.number_input("Base Salary (₹):", min_value=0, value=12000)
            n_jdate = st.date_input("Joining Date:", value=datetime.now(KOLKATA_TZ).date())
            
            sh_h = st.selectbox("Hour:", [f"{i:02d}" for i in range(1, 13)], index=8)
            sh_m = st.selectbox("Minute:", [f"{i:02d}" for i in range(0, 60, 5)], index=0)
            sh_p = st.selectbox("Period:", ["AM", "PM"], index=0)
            final_shift = f"{sh_h}:{sh_m} {sh_p}"
            
            if st.button("Create Account", type="primary"):
                if n_id in all_users:
                    st.error("ID Already Exists!")
                elif n_id == "" or n_name == "" or n_pass == "":
                    st.error("Please fill all fields!")
                else:
                    add_user_to_db(n_id, n_name, n_pass, n_sal, final_shift, str(n_jdate))
                    st.success("Employee Added!")
                    st.rerun()
                    
        st.markdown("---")
        
        report_rows = []
        for uid, udata in all_users.items():
            if udata["Role"] == "Employee":
                f_days, h_days, hol_days, a_days, l_days, p_sal, ded = calculate_salary_report(uid, udata['Base_Salary'], udata.get('Joining_Date', '2026-01-01'))
                next_pay = get_next_salary_date(udata.get('Joining_Date', '2026-01-01'))
                report_rows.append({
                    "ID": str(uid), "Name": udata["Name"], "Joining_Date": udata.get('Joining_Date', '2026-01-01'),
                    "Salary_Due": next_pay, "Shift": udata["Shift_Time"], "Salary": udata["Base_Salary"],
                    "Full": f_days, "Half": h_days, "Late": l_days, "Payable": p_sal, "Absent": a_days
                })
        df_report = pd.DataFrame(report_rows)
        
        st.subheader("🔎 Search Employee Profile")
        q = st.text_input("Enter ID or Name:", key="live_q").strip().lower()
        
        df_to_show = df_report
        if q and not df_report.empty:
            df_to_show = df_report[df_report["ID"].str.lower().str.contains(q) | df_report["Name"].str.lower().str.contains(q)]
            
        st.subheader("📊 Live Employee Salary & Stats Overview")
        if not df_to_show.empty:
            for _, row in df_to_show.iterrows():
                eid = str(row["ID"])
                st.write(f"📅 Join: {row['Joining_Date']} | 🗓️ Next Cycle: {row['Salary_Due']}")
                
                cs1, cs2, cs3, cs4, cs5, cs6, cs7 = st.columns([1, 1.8, 1.1, 1.1, 1.1, 1.2, 1.4])
                cs1.write(f"ID: {eid}")
                cs2.write(f"Name: {row['Name']}")
                cs3.write(f"🟢 Full: {row['Full']}")
                cs4.write(f"🟡 Half: {row['Half']}")
                cs5.write(f"❌ Abs: {row['Absent']}")
                cs6.write(f"⚠️ Late: {row['Late']}")
                cs7.write(f"💰 Pay: ₹{row['Payable']}")
                
                cb1, cb2 = st.columns(2)
                with cb1:
                    if st.button("🔄 Paid & Reset", key=f"p_{eid}"):
                        clear_employee_attendance(eid)
                        st.success("Reset Completed!")
                        st.rerun()
                with cb2:
                    if st.button("🗑️ Delete Account", key=f"d_{eid}"):
                        delete_user_from_db(eid)
                        st.warning("Account Deleted!")
                        st.rerun()
                st.markdown("---")
        else:
            st.info("No records found.")

        df_att = get_attendance()
        if not df_att.empty:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                df_att.to_excel(writer, index=False, sheet_name='Sheet1')
            st.download_button(label="📥 Download Master Sheets (.xlsx)", data=buf.getvalue(), file_name="Master_Attendance.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        st.subheader("🖨️ Official Showroom QR Code")
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={SHOWROOM_QR_SECRET}", width=300)
        
        st.subheader("📋 System Logs Database")
        st.dataframe(df_att, use_container_width=True)

# --- 2. SIGN IN SCREEN ---
else:
    st.subheader("🔒 Sign In to Portal")
    st.info("প্রথমবার ব্যবহারের জন্য আইডি এবং পাসওয়ার্ড দিয়ে লগইন সম্পন্ন করুন।")
    
    l_id = st.text_input("User ID No:", key="login_uid_field").strip()
    l_pass = st.text_input("Password:", type="password", key="login_pass_field").strip()
    
    if st.button("Verify & Login", type="primary"):
        if l_id in all_users and str(all_users[l_id]["Password"]) == l_pass:
            st.session_state.logged_in_uid = l_id
            st.session_state.is_pin_unlocked = False
            st.success("Logging in...")
            st.rerun()
        else:
            st.error("❌ ভুল আইডি অথবা পাসওয়ার্ড!")
