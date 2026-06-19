import streamlit as st
import serial

from datetime import datetime
import time
import json

# =========================================================
# 아두이노 연결
# =========================================================

@st.cache_resource
def get_ser(port):
    try:
        return serial.Serial(port, 115200, timeout=1)
    except:
        return None

port = st.sidebar.text_input("시리얼 포트", value="COM3")

st.session_state.ser = get_ser(port)

if st.session_state.ser is not None:
    st.sidebar.success(f"{port} 연결 성공!")
else:
    st.sidebar.error(f"{port}를 찾을 수 없습니다.")


# =========================================================
# 상태 초기화
# =========================================================

if "passages" not in st.session_state:
    st.session_state.passages = []

# =========================================================
# 데이터 수집
# =========================================================
def fetch_data():
    ser = st.session_state.ser
    if ser is not None and ser.is_open:
        while ser.in_waiting > 0:
            try:
                message = ser.readline().decode("utf-8").strip()
                if not message:
                    continue
                payload = json.loads(message)
                if payload.get("type") == "gate":
                    st.session_state.passages.append({
                        "time": datetime.now(),
                        "event": payload["event"],
                    })
            except Exception as e:
                st.sidebar.error(e)

with st.sidebar:
    @st.fragment(run_every="1s")
    def collect_data():
        fetch_data()

    collect_data()

# =========================================================
# 페이지 내비게이션 및 앱 실행
# =========================================================

pages = [
    st.Page("dashboard.py", title="대시보드", icon=":material/dashboard:", default=True),
]

page = st.navigation(pages=pages)

st.title(f"{page.icon} {page.title}")

page.run()
