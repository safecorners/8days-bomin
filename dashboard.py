import streamlit as st
import pandas as pd


@st.fragment(run_every="1s")
def display_data():
    records = st.session_state.get("passages", [])

    st.caption("아두이노가 보낸 입장/퇴장 이벤트로 급식실 인원을 실시간 집계합니다.")

    if not records:
        st.info("아직 들어온 데이터가 없습니다.")
        return

    df = pd.DataFrame(records)   # 열: time, event

    # 1) 누적 인원: in이면 +1, out이면 -1 (0명 아래로는 내려가지 않게)
    occupancy = 0
    history = []
    for event in df["event"]:
        if event == "in":
            occupancy += 1
        elif event == "out" and occupancy > 0:
            occupancy -= 1
        history.append(occupancy)
    df["occupancy"] = history

    # 2) 현재 상태 지표
    c1, c2, c3 = st.columns(3)
    c1.metric("현재 인원", int(df["occupancy"].iloc[-1]))
    c2.metric("누적 입장", int((df["event"] == "in").sum()))
    c3.metric("누적 퇴장", int((df["event"] == "out").sum()))

    # 3) 현재 인원 추이 그래프
    st.subheader("현재 인원 추이")
    st.line_chart(df.set_index("time")["occupancy"])

    # 4) 시간대별 입장 수 — 도착이 몰리는 때가 곧 혼잡한 때
    st.subheader("시간대별 입장 수")
    bucket = st.selectbox("집계 단위", ["10초", "1분", "10분", "1시간"], index=1)
    rule = {"10초": "10s", "1분": "1min", "10분": "10min", "1시간": "1h"}[bucket]

    ins = df[df["event"] == "in"]
    if ins.empty:
        st.info("아직 입장 기록이 없습니다.")
    else:
        per_bucket = ins.set_index("time")["event"].resample(rule).count()
        st.bar_chart(per_bucket)

    # 5) 최근 출입 기록
    st.subheader("최근 출입 기록")
    st.dataframe(
        df[["time", "event"]].sort_values("time", ascending=False).head(20),
        hide_index=True,
    )


display_data()