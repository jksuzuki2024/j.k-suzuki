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

if not st.session_state.logged_in:
    st.subheader("🔒 User Login")
    col1, col2 = st.columns(2)
    with col1:
        login_id = st.text_input("Enter your ID No:").strip()
    with col2:
        login_pass = st.text_input
