import streamlit as st
import serial
import json
from datetime import datetime
import pandas as pd
import time

st.title("Dashboard")

port = st.text_input("시리얼 포트", value="COM3")

@st.cache_resource
def get_ser(port):
    try:
        return serial.Serial(port, 115200, timeout=1)
    except:
        return None

ser = get_ser(port)

if ser is not None:
    st.success(f"{port} 연결 성공!")
else:
    st.error(f"{port}를 찾을 수 없습니다.")


if "raw_data" not in st.session_state:
    st.session_state.raw_data = []

@st.fragment(run_every="1s")
def sync_data():
    if ser and ser.is_open and ser.in_waiting > 0:
        try:
            message = ser.readline().decode("utf-8").strip() 
            payload = json.loads(message)

            sensor_type = payload["type"]
            sensor_value = payload["value"]
            
            new_entry = {
                    "time": datetime.now(),
                    sensor_type: sensor_value,
            }

            st.session_state.raw_data.append(new_entry)

        except Exception as e:
            st.sidebar.error(e)

    count = len(st.session_state.raw_data)
    st.caption(f"수집된 데이터 개수: {count}")

    if st.session_state.raw_data:
        df = pd.DataFrame(st.session_state.raw_data).set_index("time")
        df = df[-30:]
        st.line_chart(df)

        if "light" in df.columns:
            current_value = df["light"][-1]
            max_value = df["light"].max()
            min_value = df["light"].min()
            avg_value = df["light"].mean()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("현재값", current_value)
            col2.metric("최대값", max_value)
            col3.metric("최소값", min_value)
            col4.metric("평균값", f"{avg_value:0.0f}")

        with st.expander("원본 데이터 보기"):
            st.dataframe(df)

sync_data()


angle = st.slider("각도", 0, 180, 90, disabled=(ser is None))

if "prev_angle" not in st.session_state:
    st.session_state.prev_angle = 90

if angle != st.session_state.prev_angle:
    
    payload = {
        "type": "servo",
        "angle":angle,
    }
    message = json.dumps(payload)

    if ser and ser.is_open:
        ser.write(message.encode())
        st.session_state.prev_angle = angle

with st.expander("JSON"):
    current_payload = {
        "type": "servo",
        "angle":angle,
    }
    st.code(json.dumps(current_payload, indent=2), language="json")
