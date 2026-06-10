import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import io

# Timezone Kolkata
KOLKATA_TZ = pytz.timezone("Asia/Kolkata")
SHOWROOM_QR_SECRET = "JK_SUZUKI_SHOWROOM_OFFICIAL_ATTENDANCE_2026"

# এই আইডি-পাসওয়ার্ডগুলো কোডের ভেতরেই আজীবনের জন্য ফিক্সড করে দেওয়া হলো
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

st.set_page_config(page_title="JK Suzuki Management", layout="wide")
st.title("🏍️ JK Suzuki Attendance & Salary System")
st.markdown("---")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = ""

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
    
    if st.sidebar.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.rerun()

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

    elif user_info['Role'] == "Admin":
        st.subheader("👑 Owner / Admin Control Panel")
        
        st.markdown("### 📥 Download Attendance Data")
        if not att_df.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                att_df.to_excel(writer, index=False, sheet_name='Attendance_Sheet')
            st.download_button(label="📥 Click to Download Excel File (.xlsx)", data=buffer.getvalue(), file_name=f"JK_Suzuki_Attendance.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        else:
            st.info("No attendance recorded yet.")
            
        st.markdown("---")
        
        # বিশ্বস্ত অনলাইন এপিআই দিয়ে কিউআর কোড (এটি কখনো ক্রাশ করবে না)
        with st.expander("🖨 Showroom Official QR Code (প্রিন্ট করার জন্য ক্লিক করুন)"):
            st.write("নিচের কিউআর কোডটি মোবাইল দিয়ে ছবি তুলে দেওয়ালে লাগিয়ে দিন।")
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={SHOWROOM_QR_SECRET}"
            st.image(qr_url, caption="JK Suzuki QR Code", width=300)
            
        st.markdown("---")
        st.subheader("📋 Overall Live Attendance Sheet")
        st.dataframe(att_df, use_container_width=True)
