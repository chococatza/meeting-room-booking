import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# Configuration
CREDS_FILE = "creds_template.json"
ROOMS = ["ATLANTIC", "PACIFIC", "ARCTIC", "SOUTHERN"]
SHEET_URL = "https://docs.google.com/spreadsheets/d/12eLYWCI6O127XuMQP2c7g9IRfrqlu0_xz0K5WpPBbfk/edit"

# Auth
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(SHEET_URL).sheet1

# UI
st.set_page_config(page_title="จองห้องประชุม", layout="centered")
st.title("📅 จองห้องประชุม")

# Load data
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Form input
date = st.date_input("📆 วันที่")
time_range = st.text_input("⏰ เวลา (เช่น 10:00-11:00)")
room = st.selectbox("🏢 ห้องประชุม", ROOMS)
booked_by = st.text_input("👤 ชื่อผู้จอง")

if st.button("✅ จองห้องประชุม"):
    date_str = date.strftime("%Y-%m-%d")

    # แยกเวลาเริ่ม–สิ้นสุด
    try:
        start_str, end_str = [t.strip() for t in time_range.split("-")]
        start_time = datetime.strptime(start_str, "%H:%M")
        end_time = datetime.strptime(end_str, "%H:%M")
        if end_time <= start_time:
            st.error("⛔ เวลาสิ้นสุดต้องหลังเวลาเริ่ม")
            st.stop()
    except Exception as e:
        st.error(f"❌ กรอกเวลาไม่ถูกต้อง เช่น 10:00-11:00 ({e})")
        st.stop()

    # ตรวจเวลาทับซ้อน
    def is_time_overlap(start1, end1, start2, end2):
        return start1 < end2 and start2 < end1

    conflict = None
    for _, row in df[df["Date"] == date_str].iterrows():
        if row["Room"] != room:
            continue
        try:
            exist_start_str, exist_end_str = [t.strip() for t in row["Time"].split("-")]
            exist_start = datetime.strptime(exist_start_str, "%H:%M")
            exist_end = datetime.strptime(exist_end_str, "%H:%M")
            if is_time_overlap(start_time, end_time, exist_start, exist_end):
                conflict = row
                break
        except Exception as e:
            st.warning(f"⛔ เวลาในข้อมูลเก่าไม่ถูกต้อง: {e}")

    if conflict is not None:
        st.error(f"❌ ห้องนี้ถูกจองแล้วโดย {conflict['Booked By']} เวลา {conflict['Time']}")
    else:
        sheet.append_row([date_str, time_range.strip(), room, booked_by])
        st.success("✅ จองห้องสำเร็จแล้ว!")

# Show all bookings
with st.expander("📖 รายการจองทั้งหมด"):
    st.dataframe(df)
