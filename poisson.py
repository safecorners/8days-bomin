import streamlit as st
import pandas as pd
import simpy
import random

# =========================================================
# 급식실 혼잡도 시뮬레이터 (SimPy)
#
# 학생들은 "포아송 과정"으로 띄엄띄엄 도착한다.
# 즉, 평균 도착 간격은 정해져 있지만 매 순간은 무작위다.
# 이렇게 도착한 학생들이 배식대(=공유 자원)를 두고 줄을 서면서
# 혼잡이 생긴다. 그 혼잡을 SimPy로 흉내 내 본다.
# =========================================================

# ---------------------------------------------------------
# 1) 사이드바 — 시뮬레이션 설정값
# ---------------------------------------------------------
st.sidebar.subheader("시뮬레이션 설정")

arrival_rate = st.sidebar.slider("도착률 λ (명/분)", 0.5, 10.0, 3.0, 0.5)
avg_service_time = st.sidebar.slider("평균 배식 시간 (분)", 0.1, 3.0, 0.5, 0.1)
num_counters = st.sidebar.slider("배식대 수", 1, 6, 2)
sim_time = st.sidebar.slider("시뮬레이션 시간 (분)", 10, 120, 60, 10)
seed = st.sidebar.number_input("난수 시드", value=42, step=1)


# ---------------------------------------------------------
# 2) SimPy 모델 — "학생 한 명의 일생"을 이야기로 쓴다
# ---------------------------------------------------------
def student(env, name, counters, people):
    arrival = env.now                       # 도착한다
    with counters.request() as 차례:         # 줄에 선다
        yield 차례                           # 내 차례를 기다린다
        wait = env.now - arrival            # 여기까지 기다린 시간
        yield env.timeout(random.expovariate(1 / avg_service_time))  # 배식만큼 머문다
    # with 블록이 끝나면 배식대를 반납하고 떠난다
    people.append({
        "name": name,
        "arrival": round(arrival, 2),
        "wait_time": round(wait, 2),
    })


def arrivals(env, counters, people):
    # 포아송 과정: 다음 학생까지의 간격을 무작위로 뽑아 계속 도착시킨다
    n = 0
    while True:
        yield env.timeout(random.expovariate(arrival_rate))  # 다음 학생까지 간격
        n += 1
        env.process(student(env, f"학생{n}", counters, people))


def monitor(env, counters, timeline, interval=1.0):
    # 1분마다 급식실 상태를 사진 찍듯 기록한다
    while True:
        timeline.append({
            "time": round(env.now, 1),
            "queue_length": len(counters.queue),  # 줄 서서 기다리는 사람
            "in_service": counters.count,         # 지금 배식 받는 사람
        })
        yield env.timeout(interval)


# ---------------------------------------------------------
# 3) 시뮬레이션 실행
# ---------------------------------------------------------
random.seed(seed)
env = simpy.Environment()
counters = simpy.Resource(env, capacity=num_counters)

people = []     # 학생별 기록
timeline = []   # 시간대별 상태

env.process(arrivals(env, counters, people))
env.process(monitor(env, counters, timeline))
env.run(until=sim_time)

df_people = pd.DataFrame(people)
df_time = pd.DataFrame(timeline)

st.caption("학생들을 포아송 과정으로 도착시켜 급식실 혼잡도를 시뮬레이션합니다.")

if df_people.empty:
    st.info("이 설정에서는 도착한 학생이 없습니다. 도착률이나 시뮬레이션 시간을 늘려 보세요.")
    st.stop()


# ---------------------------------------------------------
# 4) 결과 — 혼잡도 지표
# ---------------------------------------------------------
c1, c2, c3 = st.columns(3)
c1.metric("총 이용 학생", len(df_people))
c2.metric("평균 대기 시간(분)", round(df_people["wait_time"].mean(), 2))
c3.metric("최대 대기열", int(df_time["queue_length"].max()))


# ---------------------------------------------------------
# 5) 시간대별 혼잡도
# ---------------------------------------------------------
st.subheader("시간대별 혼잡도")
st.line_chart(df_time.set_index("time")[["queue_length", "in_service"]])
st.caption("줄 선 사람(queue_length)이 길어지는 때가 곧 혼잡한 때입니다.")


# ---------------------------------------------------------
# 6) 분당 도착 학생 수 분포 (= 포아송 분포)
# ---------------------------------------------------------
st.subheader("분당 도착 학생 수 분포 (포아송 분포)")

# 각 학생이 몇 분에 도착했는지 → 1분 구간마다 도착 수를 센다 (0명인 분도 포함)
도착수 = df_people["arrival"].astype(int).value_counts().reindex(range(sim_time), fill_value=0)
# 그 도착 수가 0명, 1명, 2명... 인 분이 각각 몇 번이었나
분포 = (
    도착수.value_counts()
    .sort_index()
    .rename_axis("1분 동안 온 학생 수")
    .reset_index(name="그런 분이 몇 번")
)

st.bar_chart(분포, x="1분 동안 온 학생 수", y="그런 분이 몇 번")
st.caption(
    f"한 명씩 무작위로 도착시켰을 뿐인데 분당 도착 수는 포아송 분포 모양을 이룹니다. "
    f"실제 평균 {도착수.mean():.2f}명 ≈ 설정한 도착률 {arrival_rate}명/분"
)


# ---------------------------------------------------------
# 7) 학생별 기록
# ---------------------------------------------------------
st.subheader("학생별 기록")
st.dataframe(df_people, hide_index=True)


# ---------------------------------------------------------
# 8) 학습자용 코드 해설
# ---------------------------------------------------------
with st.expander("이 시뮬레이션은 어떻게 동작하나요?"):
    st.markdown(
        """
이 시뮬레이션의 주인공은 **학생 한 명**입니다. 학생의 일생은 이렇게 흘러갑니다.

```python
arrival = env.now            # 도착한다
with counters.request() as 차례:
    yield 차례               # 내 차례를 기다린다 (← 줄 서기)
    yield env.timeout(...)   # 배식 시간만큼 머문다
# 떠난다 (with 블록이 끝나면 배식대를 자동으로 반납)
```

- **도착**: `random.expovariate(λ)` 로 다음 학생까지의 간격을 무작위로 뽑습니다.
  평균 간격은 일정하지만 순간순간은 들쭉날쭉 — 이것이 **포아송 과정**입니다.
- **배식대**: `simpy.Resource(capacity=배식대 수)` 가 줄(FIFO)을 알아서 관리합니다.
  자리가 없으면 `yield 차례` 에서 자동으로 기다립니다.
- **혼잡도**: 도착이 배식 속도보다 빠르면 줄(`queue`)이 쌓입니다.
  배식대 수를 줄이거나 도착률을 높여 보면 혼잡이 어떻게 커지는지 보입니다.
        """
    )
