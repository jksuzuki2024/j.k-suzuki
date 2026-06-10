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
        "admin": {"Name": "Showroom Owner", "Password": "admin786", "Role": "Admin", "Base_Salary": 0, "Shift_Time": "09:00 AM", "Joining_Date": "2026-01-01"},
        "101": {"Name": "Amit Kumar", "Password": "password101", "Role": "Employee", "Base_Salary": 15000, "Shift_Time": "09:00 AM", "Joining_Date": "2026-01-01"},
        "102": {"Name": "Rahul Singh", "Password": "password102", "Role": "Employee", "Base_Salary": 12000, "Shift_Time": "09:30 AM", "Joining_Date": "2026-01-05"},
        "114": {"Name": "Jahir", "Password": "jahir", "Role": "Employee", "Base_Salary": 12000, "Shift_Time": "10:00 AM", "Joining_Date": "2026-01-10"}
    }
    if not os.path.exists(DB_FILE):
        rows = [{"ID": str(k), "Name": v["Name"], "Password": str(v["Password"]), "Role": v["Role"], "Base_Salary": float(v["Base_Salary"]), "Shift_Time": v["Shift_Time"], "Joining_Date": v["Joining_Date"]} for k, v in fixed_accounts.items()]
        pd.DataFrame(rows).to_excel(DB_FILE, index=False)
    else:
        df = pd.read_excel(DB_FILE)
        if "Joining_Date" not in df.columns:
            df["Joining_Date"] = "2026-01-01"
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
    return {
        str(row["ID"]).strip(): {
            "Name": row["Name"], 
            "Password": str(row["Password"]).strip(), 
            "Role": row["Role"], 
            "Base_Salary": float(row["Base_Salary"]), 
            "Shift_Time": str(row["Shift_Time"]),
            "Joining_Date": str(row["Joining_Date"])
        } for _, row in df.iterrows()
    }

def add_user_to_db(uid, name, password, base_salary, shift_time, joining_date):
    df = pd.read_excel(DB_FILE)
    new_row = pd.DataFrame(
