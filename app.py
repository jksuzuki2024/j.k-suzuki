import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz
import io

# Timezone Kolkata set kora holo
KOLKATA_TZ = pytz.timezone("Asia/Kolkata")

# Shroom er nijossho fixed QR content
SHOWROOM_QR_SECRET = "JK_SUZUKI_SHOWROOM_OFFICIAL_ATTENDANCE_2026"

DEFAULT_USERS = pd.DataFrame([
    {"ID": "101", "Name": "Amit Kumar", "Password": "password101", "Role": "Employee", "Base_Salary": 15000},
    {"ID": "102", "Name": "Rahul Singh", "Password": "password102", "Role": "Employee", "Base_Salary": 12000},
    {"ID": "admin", "Name": "Showroom Owner", "Password": "admin786", "Role": "Admin", "Base_Salary": 0}
])

# Initialize global session memory for persistent local storage
if "attendance_list" not in st.session_state:
    st.session_state.attendance_list = []

# Core Logic: Session memory converted to DataFrame
if st.session_state.attendance_list:
    att_df = pd.DataFrame(st.session_state.attendance_list)
else:
    att_df = pd.DataFrame(columns=["Date", "ID", "Name", "Entry Time", "Exit Time", "Status"])

user_df = DEFAULT_USERS.copy()

def calculate_emp_salary(emp_id, base_salary, att_dataframe):
    total_days = 30 
    allowed_holidays = 4 
    
    if not att_dataframe.empty and "ID" in att_dataframe.columns:
        emp_logs = att_dataframe[att_dataframe["ID"] == str(emp_id)]
        present_days = emp_logs["Date"].nunique() if not emp_logs.empty else 0
    else:
        present_days = 0
        
    paid_days = min(present_days + allowed_holidays, total_days)
    absent_days = max(0, total_days - paid_days)
    
    per_day_salary = base_salary / total_days
    payable_salary = round(paid_days * per_day_salary, 2)
    deduction = round(absent_days * per_day_salary, 2)
    
    return present_days, allowed_holidays, absent_days, payable_salary, deduction

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
    st.sidebar.subheader(f"👤 Profile: {st.session_state.user_name}")
    st.sidebar.write(f"**ID No:** {st.session_state.user_id}")
    st.sidebar.write(f"**Role:** {st.session_state.user_role}")
    
    if st.session_state.user_role == "Employee":
        emp_info = user_df[user_df["ID"] == st.session_state.user_id]
        if not emp_info.empty:
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
        st.rerun()

    # ==================== 1. Employee Screen ====================
    if st.session_state.user_role == "Employee":
        st.subheader("📷 Shroom Live Attendance Scanner")
        from streamlit_qrcode_scanner import qrcode_scanner
        
        now_kolkata = datetime.now(KOLKATA_TZ)
        current_date = str(now_kolkata.date())
        current_time = now_kolkata.strftime("%I:%M %p")
        
        st.info(f"📅 **Today's Date:** {current_date} | ⏰ **Kolkata Time:** {current_time}")
        current_user_id = str(st.session_state.user_id).strip()
        
        today_entry = att_df[(att_df["Date"] == current_date) & (att_df["ID"] == current_user_id)] if not att_df.empty else pd.DataFrame()
        
        if today_entry.empty:
            st.warning("📋 আপনার আজকের হাজিরা দেওয়া হয়নি। শোরুমের QR Code টি লাইভ স্ক্যান করুন।")
            qr_code_value = qrcode_scanner(key='qr_scanner_entry')
            
            if qr_code_value:
                if qr_code_value == SHOWROOM_QR_SECRET:
                    new_row = {
                        "Date": current_date, "ID": current_user_id, "Name": st.session_state.user_name,
                        "Entry Time": current_time, "Exit Time": "Not Out Yet", "Status": "Present"
                    }
                    st.session_state.attendance_list.append(new_row)
                    st.success("✅ ENTRY Recorded Successfully in Dashboard memory!")
                    st.rerun()
                else:
                    st.error("❌ ভুল QR Code!")
                    
        elif today_entry.iloc[0]["Exit Time"] == "Not Out Yet":
            st.info("⚠️ ছুটির সময় বিদায় নেওয়ার জন্য আবার শোরুমের QR Code টি লাইভ স্ক্যান করুন।")
            qr_code_value = qrcode_scanner(key='qr_scanner_exit')
            
            if qr_code_value:
                if qr_code_value == SHOWROOM_QR_SECRET:
                    for record in st.session_state.attendance_list:
                        if record["Date"] == current_date and record["ID"] == current_user_id:
                            record["Exit Time"] = current_time
                    st.success("✅ EXIT Recorded Successfully in Dashboard memory!")
                    st.rerun()
        else:
            st.success("🎉 Today's Attendance Completed!")
            
        st.markdown("---")
        st.subheader("📊 Your Personal Logs")
        st.dataframe(att_df[att_df["ID"] == current_user_id], use_container_width=True)

    # ==================== 2. Admin Screen ====================
    elif st.session_state.user_role == "Admin":
        st.subheader("👑 Owner / Admin Control Panel")
        
        # EXCEL GENERATOR & DOWNLOAD BUTTON FOR COMPUTER
        st.markdown("### 📥 Download Attendance Data to Microsoft Excel")
        if not att_df.empty:
            # InMemory bytes conversion for pure excel .xlsx framework
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                att_df.to_excel(writer, index=False, sheet_name='Attendance_Sheet')
            
            st.download_button(
                label="📥 Click to Download Microsoft Excel File (.xlsx)",
                data=buffer.getvalue(),
                file_name=f"JK_Suzuki_Attendance_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.info("No attendance recorded yet to download.")
            
        st.markdown("---")
        with st.expander("🖨 Showroom Official QR Code"):
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={SHOWROOM_QR_SECRET}")
        
        search_id = st.text_input("🔍 Search Employee ID:").strip()
        if search_id != "":
            emp_info = user_df[user_df["ID"] == str(search_id)]
            if not emp_info.empty:
                emp_name = emp_info.iloc[0]["Name"]
                base_sal = emp_info.iloc[0]["Base_Salary"]
                p_days, h_days, a_days, p_sal, ded = calculate_emp_salary(search_id, base_sal, att_df)
                
                st.subheader(f"📊 Report of {emp_name}")
                st.write(f"Present: {p_days} Days | Base: ₹{base_sal} | **Net Payable: ₹{p_sal}**")
        
        st.markdown("---")
        st.subheader("📋 Overall Live Attendance Sheet")
        st.dataframe(att_df, use_container_width=True)
