import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Netflix Non-English TV Analytics", layout="wide")
st.title("🎬 Netflix Non-English TV Interactive Dashboard")

# 1. 데이터 로드
@st.cache_data
def load_all_data():
    macro = pd.read_csv('data/processed/01_weekly_macro_series.csv')
    macro['week'] = pd.to_datetime(macro['week'])
    macro['hours_sma_12w'] = macro['weekly_hours_viewed'].rolling(window=12).mean()
    
    show_summary = pd.read_csv('data/processed/02_show_retention_summary.csv')
    df_decay = pd.read_csv('data/processed/03_decay_normalized.csv')
    return macro, show_summary, df_decay

macro_df, show_summary, df_decay = load_all_data()

# 2. 사이드바 인터랙티브 필터
st.sidebar.header("🔍 인터랙티브 필터")
min_year = int(macro_df['week'].dt.year.min())
max_year = int(macro_df['week'].dt.year.max())

selected_years = st.sidebar.slider(
    "조회 연도 범위 선택",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

filtered_macro = macro_df[
    (macro_df['week'].dt.year >= selected_years[0]) & 
    (macro_df['week'].dt.year <= selected_years[1])
]

# 3. 상단 핵심 KPI 요약 카드
col1, col2, col3, col4 = st.columns(4)
col1.metric("선택 기간 총 주차", f"{len(filtered_macro)} 주")
col2.metric("평균 주간 시청 시간", f"{filtered_macro['weekly_hours_viewed'].mean() / 1e6:.1f} M 시간")
col3.metric("최고 주간 시청 시간", f"{filtered_macro['weekly_hours_viewed'].max() / 1e6:.1f} M 시간")
col4.metric("주간 변동성(WoW 표준편차)", f"{filtered_macro['wow_pct_change'].std():.1f}%")

st.markdown("---")

# 4. 분석 탭 분할 구성
tab1, tab2, tab3 = st.tabs(["📈 시계열 트렌드 & 변동성", "📦 롱런작 수명 분포", "⏳ 피크 후 반감기(Half-Life) 분석"])

with tab1:
    # 3-Line 시계열 트렌드
    st.subheader("1. 주간 시청 시간 및 이동평균 (3-Line Trend)")
    fig1, ax1 = plt.subplots(figsize=(14, 4.5))
    ax1.plot(filtered_macro['week'], filtered_macro['weekly_hours_viewed'] / 1e6, color='#C0C0C0', alpha=0.6, label='Raw Weekly Hours')
    ax1.plot(filtered_macro['week'], filtered_macro['hours_sma_4w'] / 1e6, color='#0055FF', linewidth=2.0, label='4-Week SMA (Blue)')
    ax1.plot(filtered_macro['week'], filtered_macro['hours_sma_12w'] / 1e6, color='#E50914', linewidth=2.5, label='12-Week SMA (Red)')
    ax1.set_ylabel("Viewing Hours (Million)")
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='upper right')
    st.pyplot(fig1)

    # WoW 변동률 바차트
    st.subheader("2. 전주 대비 주간 증감률 변동성 (WoW % Volatility)")
    fig2, ax2 = plt.subplots(figsize=(14, 3.5))
    colors = ['#2b5c8f' if v >= 0 else '#c94c4c' for v in filtered_macro['wow_pct_change']]
    ax2.bar(filtered_macro['week'], filtered_macro['wow_pct_change'], color=colors, width=5, alpha=0.85)
    ax2.axhline(0, color='black', linewidth=0.8, linestyle='--')
    ax2.set_ylabel("WoW Growth (%)")
    ax2.set_ylim(-60, 80)
    ax2.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig2)

with tab2:
    st.subheader("차트인 기간 그룹별 총 시청 시간 분포 (로그 스케일)")
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    sns.boxplot(
        data=show_summary, x='lifecycle_group', y='total_hours_viewed', hue='lifecycle_group',
        order=['Short-run (<=4w)', 'Mid-run (5-7w)', 'Long-run (>=8w)'],
        palette={'Short-run (<=4w)': '#888888', 'Mid-run (5-7w)': '#4A90E2', 'Long-run (>=8w)': '#E50914'},
        ax=ax3, width=0.4, legend=False
    )
    ax3.set_yscale('log')
    ax3.set_xlabel("Lifecycle Group")
    ax3.set_ylabel("Total Viewing Hours (Log Scale)")
    ax3.grid(True, linestyle='--', alpha=0.5, which='both')
    st.pyplot(fig3)
    st.info("💡 상위 8.9%(59편)의 롱런작이 전체 시청 시간의 42.7%를 점유하고 있음을 보여줍니다.")

with tab3:
    st.subheader("메가히트작 피크 이후 반감기(Half-Life) 감쇄 곡선")
    
    # 작품 다중 선택 필터
    available_shows = df_decay['show_title'].unique().tolist()
    selected_shows = st.multiselect("비교할 작품 선택", options=available_shows, default=available_shows)
    
    fig4, ax4 = plt.subplots(figsize=(10, 5))
    palette_colors = {'Squid Game': '#E50914', 'Money Heist': '#F5A623', 'Extraordinary Attorney Woo': '#2E7D32'}
    
    for show in selected_shows:
        sub = df_decay[df_decay['show_title'] == show]
        col = palette_colors.get(show, '#555555')
        ax4.plot(sub['weeks_since_peak'], sub['normalized_pct'], label=show, color=col, marker='o', linewidth=2)
        
    ax4.axhline(50, color='black', linestyle='--', linewidth=1.2, label='Half-Life Threshold (50%)')
    ax4.set_xlabel("Weeks Elapsed Since Peak")
    ax4.set_ylabel("% of Peak Viewership")
    ax4.set_xlim(-0.5, 15)
    ax4.legend(loc='upper right')
    ax4.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig4)