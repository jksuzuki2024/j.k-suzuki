import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz
import io
import qrcode
from PIL import Image

# Timezone Kolkata
KOLKATA_TZ = pytz.timezone("Asia/Kolkata")

# Fixed QR Secret
SHOWROOM_QR_SECRET = "JK_SUZUKI_SHOWROOM_OFFICIAL_ATTENDANCE_2026"

# Permament ID-Password Backup (Apnar shob ID ekhane permanent safe thakbe)
FIXED_ACCOUNTS = {
    "admin": {"Name": "Showroom Owner", "Password": "admin786", "Role": "Admin", "Base_Salary": 0},
    "101": {"Name": "Amit Kumar", "Password": "password101", "Role": "Employee", "Base_Salary": 15000},
    "102": {"Name": "Rahul Singh", "Password": "password102", "Role": "Employee", "Base_Salary": 12000},
    "114": {"Name": "Jahir", "Password": "jahir", "Role": "Employee", "Base_Salary": 12000}
}

if "custom_users" not in st.session_state:
    st.session_state.custom_users = FIXED_ACCOUNTS.copy()

if "attendance_records" not in st.session_state:
    st.session_state.attendance_records = []

att_df = pd.DataFrame(st.session_state.attendance_records) if st.session_state.attendance_records else pd.DataFrame(columns=["Date", "ID", "Name", "Entry Time", "Exit Time", "Status"])

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
    return present_days, allowed_holidays, absent_days, round(paid_days * per_day_salary, 2), round(absent_days * per_day_salary, 2)

st.set_page_config(page_title="JK Suzuki Management", layout="wide")
st.title("🏍️ JK Suzuki Attendance & Salary System")
st.markdown("---")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = ""

# Secure Login Flow
if not st.session_state.logged_in:
    st.subheader("🔒 User Login")
    col1, col2 = st.columns(2)
    with col1:
        login_id = st.text_input("Enter your ID No:").strip()
    with col2:
        login_pass = st.text_input("Enter Password:", type="password").strip()
        
    if st.button("Login", type="primary"):
        all_active_users = st.session_state.custom_users
        if login_id in all_active_users and str(all_active_users[login_id]["Password"]) == login_pass:
            st.session_state.logged_in = True
            st.session_state.user_id = login_id
            st.success(f"Welcome {all_active_users[login_id]['Name']}!")
            st.rerun()
        else:
            st.error("Invalid ID or Password! Please try again.")
else:
    current_uid = st.session_state.user_id
    user_info = st.session_state.custom_users[current_uid]
    
    st.sidebar.subheader(f"👤 Profile: {user_info['Name']}")
    st.sidebar.write(f"**ID No:** {current_uid}")
    st.sidebar.write(f"**Role:** {user_info['Role']}")
    
    if user_info['Role'] == "Employee":
        p_days, h_days, a_days, p_sal, ded = calculate_emp_salary(current_uid, user_info['Base_Salary'], att_df)
        st.sidebar.markdown("---")
        st.sidebar.subheader("💰 Live Salary Report")
        st.sidebar.write(f"**Base Salary:** ₹{user_info['Base_Salary']}")
        st.sidebar.write(f"**Present Today:** {p_days} Days")
        st.sidebar.success(f"**Current Payable:** ₹{p_sal}")
        if ded > 0: st.sidebar.error(f"**Deduction:** -₹{ded}")

    if st.sidebar.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.rerun()

    # Employee View
    if user_info['Role'] == "Employee":
        st.subheader("📷 Shroom Live Attendance Scanner")
        from streamlit_qrcode_scanner import qrcode_scanner
        now_kolkata = datetime.now(KOLKATA_TZ)
        current_date = str(now_kolkata.date())
        current_time = now_kolkata.strftime("%I:%M %p")
        
        st.info(f"📅 **Today's Date:** {current_date} | ⏰ **Kolkata Time:** {current_time}")
        
        today_entry = att_df[(att_df["Date"] == current_date) & (att_df["ID"] == current_uid)] if not att_df.empty else pd.DataFrame()
        
        if today_entry.empty:
            st.warning("📋 আপনার আজকের হাজিরা দেওয়া হয়নি। শোরুমের QR Code স্ক্যান করুন।")
            qr_code_value = qrcode_scanner(key='qr_scanner_entry')
            if qr_code_value and qr_code_value == SHOWROOM_QR_SECRET:
                new_row = {"Date": current_date, "ID": current_uid, "Name": user_info['Name'], "Entry Time": current_time, "Exit Time": "Not Out Yet", "Status": "Present"}
                st.session_state.attendance_records.append(new_row)
                st.success("✅ ENTRY Recorded Successfully!")
                st.rerun()
        elif today_entry.iloc[0]["Exit Time"] == "Not Out Yet":
            st.info("⚠️ ছুটির সময় বিদায় নেওয়ার জন্য আবার শোরুমের QR Code স্ক্যান করুন।")
            qr_code_value = qrcode_scanner(key='qr_scanner_exit')
            if qr_code_value and qr_code_value == SHOWROOM_QR_SECRET:
                for record in st.session_state.attendance_records:
                    if record["Date"] == current_date and record["ID"] == current_uid:
                        record["Exit Time"] = current_time
                st.success("✅ EXIT Recorded Successfully!")
                st.rerun()
        else:
            st.success("🎉 Today's Attendance Completed!")
            
        st.markdown("---")
        st.subheader("📊 Your Personal Logs")
        st.dataframe(att_df[att_df["ID"] == current_uid], use_container_width=True)

    # Admin View
    elif user_info['Role'] == "Admin":
        st.subheader("👑 Owner / Admin Control Panel")
        
        # Excel Generator
        st.markdown("### 📥 Download Attendance Data to Microsoft Excel")
        if not att_df.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                att_df.to_excel(writer, index=False, sheet_name='Attendance_Sheet')
            st.download_button(label="📥 Click to Download Microsoft Excel File (.xlsx)", data=buffer.getvalue(), file_name=f"JK_Suzuki_Attendance_{datetime.now().strftime('%d-%m-%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        else:
            st.info("No attendance recorded yet to download.")
            
        st.markdown("---")
        
        # LOCAL QR CODE GENERATOR (১০০% গ্যারান্টিড আসবেই)
        with st.expander("🖨 Showroom Official QR Code (প্রিন্ট করার জন্য ক্লিক করুন)"):
            st.write("নিচের কিউআর কোডটি ডাউনলোড বা বড় করে প্রিন্ট করে দেওয়ালে লাগিয়ে দিন।")
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(SHOWROOM_QR_SECRET)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption="JK Suzuki Official QR Code", width=300)
            
        st.markdown("---")
        with st.expander("➕ Click to Add New Employee Account (Temporary)"):
            new_id = st.text_input("New Employee ID:").strip()
            new_name = st.text_input("New Employee Full Name:").strip()
            new_pass = st.text_input("Set Password:").strip()
            new_sal = st.number_input("Monthly Base Salary:", min_value=0, value=12000)
            
            if st.button("Create Account"):
                if new_id in st.session_state.custom_users:
                    st.error("❌ This ID already exists!")
                elif new_id=="" or new_name=="" or new_pass=="":
                    st.error("❌ Please fill all fields!")
                else:
                    st.session_state.custom_users[new_id] = {"Name": new_name, "Password": new_pass, "Role": "Employee", "Base_Salary": new_sal}
                    st.success(f"✅ Account created temporary for {new_name}!")
                    st.rerun()

        st.markdown("---")
        search_id = st.text_input("🔍 Search Employee ID:").strip()
        if search_id != "" and search_id in st.session_state.custom_users:
            emp_data = st.session_state.custom_users[search_id]
            p_days, h_days, a_days, p_sal, ded = calculate_emp_salary(search_id, emp_data['Base_Salary'], att_df)
            st.subheader(f"📊 Live Salary Sheet of {emp_data['Name']}")
            st.write(f"Present: {p_days} Days | Base Salary: ₹{emp_data['Base_Salary']} | **Net Payable: ₹{p_sal}**")
        
        st.markdown("---")
        st.subheader("📋 Overall Live Attendance Sheet (All Employees)")
        st.dataframe(att_df, use_container_width=True)
