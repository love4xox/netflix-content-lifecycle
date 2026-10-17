import re
import warnings
warnings.filterwarnings('ignore')

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------------------
# [1] 스트림릿 페이지 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="넷플릭스 비영어권 TV 콘텐츠 수명 분석 대시보드",
    page_icon="🎬",
    layout="wide"
)

# 맑은 고딕 한글 폰트 및 마이너스 부호 깨짐 방지
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------------
# [2] 사이드바 테마 스위처 & 글씨 선명화
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 대시보드 환경 설정")
    theme_choice = st.radio(
        "테마 선택 (Theme):",
        options=["🌙 넷플릭스 다크 (Dark)", "☀️ 모던 비즈니스 라이트 (Light)"],
        index=0
    )
    is_dark = "다크" in theme_choice
    st.markdown("---")
    st.caption("※ 모드를 전환하면 전체 레이아웃과 차트 색상이 실시간으로 연동됩니다.")
    st.markdown("---")
    st.markdown("**📌 데이터 해석 시 주의**")
    st.caption(
        "• 넷플릭스 공식 주간 Top 10 기준이라, '총 시청 시간'은 Top 10에 든 작품의 합계이며 전체 시청이 아닙니다.\n\n"
        "• Top 10 밖인 주는 0이 아니라 '값 없음'입니다.\n\n"
        "• 언어권은 원본 컬럼이 아니라 제목 키워드로 분류한 추정치입니다."
    )

# 테마별 색상 팔레트 정의
if is_dark:
    APP_BG = "#141414"
    HEADER_BG = "#141414"
    CARD_BG = "#1F1F1F"
    TEXT_COLOR = "#FFFFFF"
    RADIO_TEXT = "#F0F0F0"
    SUB_TEXT = "#BBBBBB"
    BORDER_COLOR = "#2B2B2B"
    CHART_BG = "#1A1A1A"
    CHART_GRID = "#333333"
    SMA4_COLOR = "#4A90E2"
    ACCENT_RED = "#E50914"
    TAB_BG = "#1F1F1F"
    LEGEND_BG = "#252525"
else:
    APP_BG = "#F8F9FA"
    HEADER_BG = "#F8F9FA"
    CARD_BG = "#FFFFFF"
    TEXT_COLOR = "#212529"
    RADIO_TEXT = "#212529"
    SUB_TEXT = "#6C757D"
    BORDER_COLOR = "#E9ECEF"
    CHART_BG = "#FFFFFF"
    CHART_GRID = "#E0E0E0"
    SMA4_COLOR = "#1F4E79"
    ACCENT_RED = "#E50914"
    TAB_BG = "#E9ECEF"
    LEGEND_BG = "#FFFFFF"

# 상단 헤더 흰 띠 및 사이드바 가독성 최적화 CSS
st.markdown(f"""
<style>
    header[data-testid="stHeader"] {{
        background-color: {HEADER_BG} !important;
    }}
    .stApp {{
        background-color: {APP_BG};
        color: {TEXT_COLOR};
        font-family: -apple-system, BlinkMacSystemFont, "Malgun Gothic", "Pretendard", sans-serif;
    }}
    [data-testid="stSidebar"] {{
        background-color: {CARD_BG} !important;
        border-right: 1px solid {BORDER_COLOR};
    }}
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] span {{
        color: {RADIO_TEXT} !important;
        font-weight: 600 !important;
    }}
    h1, h2, h3, h4 {{
        color: {TEXT_COLOR} !important;
        font-weight: 700 !important;
    }}
    [data-testid="stMetric"] {{
        background-color: {CARD_BG} !important;
        border-radius: 10px !important;
        padding: 16px 20px !important;
        border-left: 5px solid {ACCENT_RED} !important;
        border-top: 1px solid {BORDER_COLOR} !important;
        border-right: 1px solid {BORDER_COLOR} !important;
        border-bottom: 1px solid {BORDER_COLOR} !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, {"0.6" if is_dark else "0.06"}) !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: {SUB_TEXT} !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }}
    [data-testid="stMetricValue"] {{
        color: {TEXT_COLOR} !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
    }}
    [data-testid="stMetricDelta"] {{
        color: {ACCENT_RED} !important;
        font-weight: 600 !important;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        border-bottom: 2px solid {BORDER_COLOR};
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {TAB_BG} !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 10px 20px !important;
        color: {SUB_TEXT} !important;
        font-weight: 600 !important;
        border: none !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {ACCENT_RED} !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }}
    .stAlert {{
        background-color: {CARD_BG} !important;
        border: 1px solid {BORDER_COLOR} !important;
        border-radius: 8px !important;
        color: {TEXT_COLOR} !important;
    }}
    [data-testid="stDataFrame"] {{
        background-color: {CARD_BG};
        border-radius: 8px;
        border: 1px solid {BORDER_COLOR};
        overflow: hidden;
    }}
</style>
""", unsafe_allow_html=True)

# 차트 테마 함수
def apply_active_chart_theme(fig, ax):
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor(CHART_BG)
    ax.tick_params(colors=TEXT_COLOR, which='both', labelsize=10)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)
    for spine in ax.spines.values():
        spine.set_color(BORDER_COLOR)
    ax.grid(True, linestyle='--', alpha=0.5, color=CHART_GRID)

# ---------------------------------------------------------
# [3] 작품명 한글 공식 번역 사전
# ---------------------------------------------------------
TITLE_KOR_MAP = {
    'Squid Game': '오징어 게임',
    'Extraordinary Attorney Woo': '이상한 변호사 우영우',
    'Alchemy of Souls': '환혼',
    'All of Us Are Dead': '지금 우리 학교는',
    'The Glory': '더 글로리',
    'Crash Landing on You': '사랑의 불시착',
    'King the Land': '킹더랜드',
    'Queen of Tears': '눈물의 여왕',
    'Physical: 100': '피지컬: 100',
    'Business Proposal': '사내맞선',
    'Doctor Cha': '닥터 차정숙',
    'My Demon': '마이 데몬',
    'Sweet Home': '스위트홈',
    'Hellbound': '지옥',
    'Mask Girl': '마스크걸',
    'Celebrity': '셀러브리티',
    'Daily Dose of Sunshine': '정신병동에도 아침이 와요',
    'Gyeongseong Creature': '경성크리처',
    'Money Heist': '종이의 집',
    'Money Heist: Korea - Joint Economic Area': '종이의 집: 공동경제구역',
    'Berlin': '베를린 (종이의 집 스핀오프)',
    'Elite': '엘리트들',
    'Lupin': '뤼팽',
    'Dark': '다크',
    '1899': '1899',
    'The Empress': '황후 엘리자베트',
    'Yo soy Betty, la fea': '베티는 못말려 (콜롬비아 원작)',
    'Café con aroma de mujer': '여인의 향기 (콜롬비아 드라마)',
    'Alice in Borderland': '아리스 인 보더랜드',
    'Demon Slayer: Kimetsu no Yaiba': '귀멸의 칼날',
    'Jujutsu Kaisen': '주술회전',
    'Attack on Titan': '진격의 거인',
    'Spy x Family': '스파이 패밀리',
    'One Piece': '원피스'
}

def get_korean_title(title):
    """정확히 일치하는 제목만 번역한다. (부분 일치는 'Dark Desire'를 '다크'로 바꾸는 등 오역을 만들어 제거)"""
    t_str = str(title).strip()
    if t_str in TITLE_KOR_MAP:
        return f"{TITLE_KOR_MAP[t_str]} ({t_str})"
    return t_str

# ---------------------------------------------------------
# [4] 데이터 로드 (캐싱)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    macro = pd.read_csv('data/processed/01_weekly_macro_series.csv')
    macro['week'] = pd.to_datetime(macro['week'])
    macro = macro.sort_values('week').reset_index(drop=True)
    macro['year'] = macro['week'].dt.year

    if 'hours_sma_12w' not in macro.columns:
        macro['hours_sma_12w'] = macro['weekly_hours_viewed'].rolling(window=12).mean()

    shows = pd.read_csv('data/processed/02_show_retention_summary.csv')
    group_map = {
        'Short-run (<=4w)': '단기작 (4주 이하)',
        'Mid-run (5-7w)': '중기작 (5~7주)',
        'Long-run (>=8w)': '롱런작 (8주 이상)'
    }
    shows['lifecycle_group_kor'] = shows['lifecycle_group'].map(group_map)

    # 04 그래프 재생성 이후 이 파일에는 Top 10 밖인 주가 빈 값(NaN)으로 들어 있다 (0이 아님)
    decay = pd.read_csv('data/processed/03_decay_normalized.csv')

    clean = pd.read_csv('data/interim/non_english_tv_clean.csv')
    clean['week'] = pd.to_datetime(clean['week'])
    clean['year'] = clean['week'].dt.year

    return macro, shows, decay, clean

try:
    weekly_macro, show_summary, df_decay_post, df_clean = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# ---------------------------------------------------------
# [5] 대시보드 헤더 & 핵심 지표 카드
# ---------------------------------------------------------
st.title("🎬 넷플릭스 비영어권 TV 콘텐츠 수명 분석 대시보드")
st.markdown(f"<p style='color:{SUB_TEXT}; margin-top:-8px; margin-bottom:25px; font-size:1.05rem;'>글로벌 주간 Top 10 시청 데이터를 기반으로 거시 시계열 트렌드, 주간 변동성 충격, 작품 수명 분포, 메가히트작 반감기를 분석합니다.</p>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
total_weeks = len(weekly_macro)
total_shows = len(show_summary)
peak_idx = weekly_macro['weekly_hours_viewed'].idxmax()
peak_macro_hours = weekly_macro.loc[peak_idx, 'weekly_hours_viewed']
peak_macro_week = weekly_macro.loc[peak_idx, 'week']
median_weekly_hours = weekly_macro['weekly_hours_viewed'].median()
mean_weekly_hours = weekly_macro['weekly_hours_viewed'].mean()

# 최고 주의 1위 작품 (카드 문구를 하드코딩하지 않고 데이터에서 찾는다)
_peak_rows = df_clean[df_clean['week'] == peak_macro_week]
peak_top_show = _peak_rows.loc[_peak_rows['weekly_hours_viewed'].idxmax(), 'show_title'] if not _peak_rows.empty else "-"

col1.metric("총 분석 주차", f"{total_weeks} 주", f"{weekly_macro['week'].min().year} ~ {weekly_macro['week'].max().year}")
col2.metric("총 분석 타이틀", f"{total_shows:,} 편", "Top 10 진입 작품 기준")
col3.metric("역대 최고 주간 시청량", f"{peak_macro_hours / 1e8:.1f}억 시간", f"{peak_macro_week.date()} · {get_korean_title(peak_top_show)}")
col4.metric("주간 시청량 중앙값", f"{median_weekly_hours / 1e8:.2f}억 시간", f"평균 {mean_weekly_hours / 1e8:.2f}억 (히트작이 평균을 끌어올림)")

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# [6] 탭 인터페이스 구성
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 주간 거시 트렌드 & 변동성",
    "📦 작품 수명 & 롱런 분석",
    "⏳ 메가히트작 반감기(Half-Life) 비교",
    "🌍 연도별 및 언어권별 점유율"
])

# ---------------------------------------------------------
# TAB 1: 주간 거시 트렌드 & 변동성 분포
# ---------------------------------------------------------
with tab1:
    st.markdown("### 1. 주간 시청 시간 추이 및 이동평균(SMA) 분석")

    fig, ax = plt.subplots(figsize=(14, 5))
    apply_active_chart_theme(fig, ax)

    raw_line_color = '#666666' if is_dark else '#CED4DA'
    ax.plot(weekly_macro['week'], weekly_macro['weekly_hours_viewed'] / 1e6,
            color=raw_line_color, alpha=0.7, linewidth=1.2, label='주간 실제 시청 시간 (원시값)')
    ax.plot(weekly_macro['week'], weekly_macro['hours_sma_4w'] / 1e6,
            color=SMA4_COLOR, linewidth=2.0, label='4주 이동평균 (단기 유행선)')
    ax.plot(weekly_macro['week'], weekly_macro['hours_sma_12w'] / 1e6,
            color=ACCENT_RED, linewidth=2.5, label='12주 이동평균 (분기 거시 추세선)')

    ax.set_title("넷플릭스 비영어권 TV 주간 Top 10 합산 시청 시간 및 이동평균 트렌드", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("기간", fontsize=11, labelpad=8)
    ax.set_ylabel("시청 시간 (백만 시간)", fontsize=11, labelpad=8)
    leg = ax.legend(loc='upper right', frameon=True, facecolor=LEGEND_BG, edgecolor=BORDER_COLOR, fontsize=10)
    for text in leg.get_texts():
        text.set_color(TEXT_COLOR)

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.markdown("### 2. 주간 증감률(WoW %) 변동성 및 충격 분포 (Volatility & Skewness)")

    valid_wow = weekly_macro['wow_pct_change'].dropna()
    skew_val = valid_wow.skew()

    fig_v, ax_v = plt.subplots(figsize=(14, 4.2))
    apply_active_chart_theme(fig_v, ax_v)

    sns.histplot(valid_wow, bins=25, kde=True, color=ACCENT_RED, ax=ax_v, alpha=0.6, edgecolor=BORDER_COLOR)
    threshold_line = '#FFFFFF' if is_dark else '#000000'
    ax_v.axvline(0, color=threshold_line, linestyle='--', linewidth=1.2, alpha=0.7, label='변동률 0% 기준선')
    ax_v.axvline(valid_wow.mean(), color='#F5A623', linestyle='-', linewidth=1.5, label=f'평균 변동률 ({valid_wow.mean():.1f}%)')

    ax_v.set_title(f"비영어권 주간 시청 시간 증감률(WoW %) 분포 (왜도 Skewness: {skew_val:.2f})", fontsize=13, fontweight='bold', pad=12)
    ax_v.set_xlabel("주간 증감률 (%)", fontsize=11, labelpad=8)
    ax_v.set_ylabel("발생 빈도 (주차 수)", fontsize=11, labelpad=8)
    leg_v = ax_v.legend(loc='upper right', frameon=True, facecolor=LEGEND_BG, edgecolor=BORDER_COLOR, fontsize=10)
    for text in leg_v.get_texts():
        text.set_color(TEXT_COLOR)

    plt.tight_layout()
    st.pyplot(fig_v, use_container_width=True)
    plt.close(fig_v)

    st.markdown("#### 📊 연도별 거시 시청 실적 및 성장률 요약")
    macro_table = weekly_macro.groupby('year').agg(
        총주차=('week', 'count'),
        연간총시청=('weekly_hours_viewed', 'sum'),
        주간평균시청=('weekly_hours_viewed', 'mean'),
        주간중앙값=('weekly_hours_viewed', 'median'),
        주간최고기록=('weekly_hours_viewed', 'max'),
        주간최저기록=('weekly_hours_viewed', 'min'),
        평균변동률=('wow_pct_change', lambda x: x.abs().mean())
    ).reset_index()

    macro_table['연도'] = macro_table['year'].apply(lambda x: f"{x}년")
    macro_table['연간 총 시청 시간'] = macro_table['연간총시청'].apply(lambda x: f"{x/1e8:.1f}억 시간")
    macro_table['주간 평균 시청 시간'] = macro_table['주간평균시청'].apply(lambda x: f"{x/1e8:.2f}억 시간")
    macro_table['주간 중앙값'] = macro_table['주간중앙값'].apply(lambda x: f"{x/1e8:.2f}억 시간")
    macro_table['주간 최고 시청 기록'] = macro_table['주간최고기록'].apply(lambda x: f"{x/1e8:.2f}억 시간")
    macro_table['주간 최저 시청 기록'] = macro_table['주간최저기록'].apply(lambda x: f"{x/1e8:.2f}억 시간")
    macro_table['평균 주간 변동폭(WoW)'] = macro_table['평균변동률'].apply(lambda x: f"±{x:.1f}%")

    st.dataframe(
        macro_table[['연도', '총주차', '연간 총 시청 시간', '주간 평균 시청 시간', '주간 중앙값', '주간 최고 시청 기록', '주간 최저 시청 기록', '평균 주간 변동폭(WoW)']],
        use_container_width=True,
        hide_index=True
    )
    st.caption("* 2021년(7월~)과 2026년(~9월)은 부분 연도라서 연간 총 시청 시간을 다른 연도와 직접 비교할 수 없습니다.")

    # 인사이트 문구: 숫자를 하드코딩하지 않고 데이터에서 계산
    sma12_series = weekly_macro.set_index('week')['hours_sma_12w'].dropna() / 1e6
    sma12_after22 = sma12_series[sma12_series.index >= '2022-01-01']
    wow_max_idx = weekly_macro['wow_pct_change'].idxmax()
    wow_max_week = weekly_macro.loc[wow_max_idx, 'week']
    wow_max_val = weekly_macro.loc[wow_max_idx, 'wow_pct_change']
    _wk_rows = df_clean[df_clean['week'] == wow_max_week]
    wow_max_show = _wk_rows.loc[_wk_rows['weekly_hours_viewed'].idxmax(), 'show_title'] if not _wk_rows.empty else "-"
    abs_wow_mean = valid_wow.abs().mean()

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.info(
            f"💡 **기본 수요 vs 메가히트 충격**: 역대 최고 주간 시청량은 {peak_macro_week.date()}의 **{peak_macro_hours / 1e6:.1f}M 시간**"
            f"(1위 작품: {get_korean_title(peak_top_show)})이고, 2022년 이후 12주 이동평균은 "
            f"**{sma12_after22.min():.1f}M ~ {sma12_after22.max():.1f}M 시간** 범위에서 움직였습니다. "
            f"주간 중앙값은 {median_weekly_hours / 1e6:.1f}M 시간으로, 평균({mean_weekly_hours / 1e6:.1f}M)보다 낮아 소수의 히트작이 평균을 끌어올립니다."
        )
    with col_t2:
        st.info(
            f"💡 **변동성 특성**: 주간 증감률(WoW)의 평균 절대 변동폭은 **±{abs_wow_mean:.1f}%**, 왜도는 **{skew_val:.2f}**로 "
            f"양의 극단값이 긴 우측 꼬리를 만듭니다. 최대 증가는 {wow_max_week.date()}의 **+{wow_max_val:.1f}%**였고, "
            f"그 주 1위 작품은 {get_korean_title(wow_max_show)}입니다. (신작 공개와의 인과는 이 데이터만으로 단정할 수 없음)"
        )

# ---------------------------------------------------------
# TAB 2: 작품 수명 & 롱런 분석
# ---------------------------------------------------------
with tab2:
    st.markdown("### 작품 수명 그룹별 누적 시청 시간 분포")

    order_kor = ['단기작 (4주 이하)', '중기작 (5~7주)', '롱런작 (8주 이상)']
    palette_kor = {'단기작 (4주 이하)': '#888888', '중기작 (5~7주)': '#4A90E2', '롱런작 (8주 이상)': '#E50914'}

    fig, ax = plt.subplots(figsize=(10, 4.8))
    apply_active_chart_theme(fig, ax)

    sns.boxplot(
        data=show_summary, x='lifecycle_group_kor', y='total_hours_viewed', hue='lifecycle_group_kor',
        order=order_kor, palette=palette_kor, ax=ax, width=0.45, legend=False, fliersize=3
    )
    ax.set_yscale('log')
    ax.set_title("수명 그룹별 누적 시청 시간 분포 (로그 스케일)", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("작품 수명 분류", fontsize=11, labelpad=8)
    ax.set_ylabel("총 누적 시청 시간 (시간, 로그 스케일)", fontsize=11, labelpad=8)

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # 그룹 구성 비율 (데이터에서 계산)
    grp_cnt = show_summary['lifecycle_group_kor'].value_counts().reindex(order_kor).fillna(0).astype(int)
    grp_pct = grp_cnt / grp_cnt.sum() * 100
    grp_text = " / ".join(f"{g} {c}편 ({p:.1f}%)" for g, c, p in zip(order_kor, grp_cnt, grp_pct))
    st.caption(f"📊 수명 그룹 구성 (총 {int(grp_cnt.sum())}편): {grp_text}")

    st.markdown("#### 🏆 글로벌 Top 10 최장기 차트인(롱런작) Top 5")
    top_longrun = show_summary.sort_values(by='max_weeks_in_top10', ascending=False).head(5).copy()
    top_longrun['total_hours_viewed'] = top_longrun['total_hours_viewed'].apply(lambda x: f"{x/1e8:.1f}억 시간")
    top_longrun['peak_hours'] = top_longrun['peak_hours'].apply(lambda x: f"{x/1e8:.1f}억 시간")
    top_longrun['작품명 (한국어)'] = top_longrun['show_title'].apply(get_korean_title)

    top_longrun_clean = top_longrun[['작품명 (한국어)', 'max_weeks_in_top10', 'total_hours_viewed', 'peak_hours', 'lifecycle_group_kor']].rename(columns={
        'max_weeks_in_top10': 'Top 10 유지 주차',
        'total_hours_viewed': '총 누적 시청 시간',
        'peak_hours': '최고 주간 시청 시간',
        'lifecycle_group_kor': '수명 분류'
    })
    st.dataframe(top_longrun_clean, use_container_width=True, hide_index=True)

    # 해설 문구도 표에서 그대로 만든다 (순위·주차를 하드코딩하지 않음)
    rank_text = ", ".join(
        f"{i}위 **{get_korean_title(t)}** ({int(w)}주)"
        for i, (t, w) in enumerate(zip(top_longrun['show_title'], top_longrun['max_weeks_in_top10']), start=1)
    )
    st.success(f"📌 **표 해설**: Top 10 최장 유지 순위는 {rank_text}입니다.")

# ---------------------------------------------------------
# TAB 3: 메가히트작 반감기(Half-Life) 비교
# ---------------------------------------------------------
with tab3:
    st.markdown("### 최고점(Peak) 이후 감쇄 곡선 및 50% 반감기 비교")

    all_decay_shows = list(df_decay_post['show_title'].unique())
    show_kor_dict = {
        'Squid Game': '오징어 게임 (시즌 1)',
        'Money Heist': '종이의 집 (파트 5)',
        'Extraordinary Attorney Woo': '이상한 변호사 우영우'
    }
    has_season_col = 'season_title' in df_decay_post.columns

    selected_shows = st.multiselect(
        "비교할 작품 선택 (추가 및 제거 가능):",
        options=all_decay_shows,
        default=all_decay_shows,
        format_func=lambda x: show_kor_dict.get(x, x)
    )

    if selected_shows:
        fig, ax = plt.subplots(figsize=(11, 4.8))
        apply_active_chart_theme(fig, ax)

        green_color = '#2ECC71' if is_dark else '#2E7D32'
        color_map = {'Squid Game': '#E50914', 'Money Heist': '#F5A623', 'Extraordinary Attorney Woo': green_color}

        max_week_plotted = 0
        for show in selected_shows:
            sub = df_decay_post[df_decay_post['show_title'] == show].sort_values('weeks_since_peak')
            kor_label = show_kor_dict.get(show, show)
            # NaN(Top 10 밖인 주)에서는 선이 끊긴다
            ax.plot(sub['weeks_since_peak'], sub['normalized_pct'],
                    label=kor_label, color=color_map.get(show, '#AAAAAA'), marker='o', linewidth=2.2)
            max_week_plotted = max(max_week_plotted, sub['weeks_since_peak'].max())

        threshold_color = '#FFFFFF' if is_dark else '#000000'
        ax.axhline(50, color=threshold_color, linestyle='--', linewidth=1.2, label='반감기 기준선 (50%)')
        ax.set_title("최고점(Week 0) 이후 주차별 시청 시간 유지율 (%)", fontsize=13, fontweight='bold', pad=12)
        ax.set_xlabel("피크 이후 경과 주차 (달력 기준, Week)", fontsize=11, labelpad=8)
        ax.set_ylabel("최고 시청 시간 대비 유지율 (%)", fontsize=11, labelpad=8)
        ax.set_xlim(-0.5, max_week_plotted + 0.5)
        ax.set_ylim(0, 105)
        leg = ax.legend(loc='upper right', frameon=True, facecolor=LEGEND_BG, edgecolor=BORDER_COLOR)
        for text in leg.get_texts():
            text.set_color(TEXT_COLOR)

        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.caption("* 선이 끊긴 구간은 해당 주에 Top 10 밖이라 값이 없는 것이며 0%가 아닙니다. 각 작품은 최고점이 속한 시즌만 사용했습니다.")

        st.markdown("#### ⏱️ 주요 메가히트작 반감기(Half-Life) 도달 현황")
        decay_summary_list = []
        for show in selected_shows:
            sub = df_decay_post[df_decay_post['show_title'] == show].sort_values('weeks_since_peak')

            # 최고 주간 시청 시간: 작품의 최고점 행이 곧 Week 0이므로 정제 데이터의 작품별 최댓값을 사용
            show_rows = df_clean[df_clean['show_title'] == show]
            peak_val = show_rows['weekly_hours_viewed'].max() if not show_rows.empty else np.nan

            # 04 그래프와 같은 기준: 유지율이 50% '미만'이 된 첫 경과 주차 (NaN은 비교에서 제외됨)
            below_50 = sub[sub['normalized_pct'] < 50]
            half_life_week = f"{int(below_50['weeks_since_peak'].min())}주 차" if not below_50.empty else "관측 구간 내 없음"

            r1 = sub.loc[sub['weeks_since_peak'] == 1, 'normalized_pct']
            ret_1w = f"{r1.iloc[0]:.0f}%" if (len(r1) and pd.notna(r1.iloc[0])) else "Top 10 밖"

            observed = int(sub['normalized_pct'].notna().sum())
            total_w = int(sub['weeks_since_peak'].max()) + 1

            row = {'작품명': show_kor_dict.get(show, show), '원제': show}
            if has_season_col:
                row['사용 시즌'] = sub['season_title'].dropna().iloc[0] if sub['season_title'].notna().any() else '-'
            row.update({
                '최고 주간 시청 시간': f"{peak_val / 1e8:.2f}억 시간" if pd.notna(peak_val) else "-",
                '정점 1주 뒤 유지율': ret_1w,
                '50% 미만 첫 경과 주차': half_life_week,
                f'Top 10 관측 주 (정점 후 {total_w}주 중)': f"{observed}주",
            })
            decay_summary_list.append(row)

        st.dataframe(pd.DataFrame(decay_summary_list), use_container_width=True, hide_index=True)
        st.info(
            "💡 **인사이트 요약 (사례 3편 기준)**: 세 작품 모두 정점 1주 뒤 유지율은 61~72%였고, 50% 미만이 되기까지 2~3주가 걸려 "
            "**정점 이후 감쇄 속도는 비슷했습니다.** 차이는 정점에 이르는 경로입니다. 오징어 게임은 첫 차트 주 +2주(11% → 78% → 100%), "
            "종이의 집은 첫 주가 정점, 우영우는 주 2회 순차 공개 속에 첫 차트 주 +6주에 정점을 찍었습니다. "
            "사례가 3편이라 순차 공개·입소문·종영 효과를 분리할 수는 없어서, 이는 원인 확정이 아닌 가설입니다."
        )

    else:
        st.warning("분석할 작품을 1개 이상 선택해 주세요.")

# ---------------------------------------------------------
# TAB 4: 연도별 및 언어권별 점유율
# ---------------------------------------------------------
with tab4:
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 연도별 주간 시청 시간 (평균 vs 중앙값)")

        yearly_agg = weekly_macro.groupby('year').agg(
            mean_hours=('weekly_hours_viewed', 'mean'),
            median_hours=('weekly_hours_viewed', 'median'),
            week_count=('week', 'count')
        ).reset_index()
        yearly_agg['year'] = yearly_agg['year'].astype(int)
        yearly_agg['week_count'] = yearly_agg['week_count'].astype(int)
        yearly_agg['mean_hours_m'] = yearly_agg['mean_hours'] / 1e6
        yearly_agg['median_hours_m'] = yearly_agg['median_hours'] / 1e6

        first_year, last_year = int(yearly_agg['year'].min()), int(yearly_agg['year'].max())
        partial_years = [first_year, last_year]

        # 부분 연도 라벨 및 해칭 분기
        year_labels = [
            f"{y}년{ '*' if y in partial_years else '' }\n(n={w}주)"
            for y, w in zip(yearly_agg['year'], yearly_agg['week_count'])
        ]
        bar_colors = ['#5C82A6' if y in partial_years else ('#1F4E79' if not is_dark else '#2980B9') for y in yearly_agg['year']]
        bar_hatches = ['//' if y in partial_years else '' for y in yearly_agg['year']]

        fig_a, ax_a = plt.subplots(figsize=(6.5, 5.0))
        apply_active_chart_theme(fig_a, ax_a)

        bars = ax_a.bar(year_labels, yearly_agg['mean_hours_m'], color=bar_colors, hatch=bar_hatches,
                        edgecolor='#1F4E79' if not is_dark else '#FFFFFF', width=0.55, alpha=0.9, label='평균')
        ax_a.plot(year_labels, yearly_agg['median_hours_m'], 'D', color='#F5A623', markersize=8,
                  markeredgecolor='white', label='중앙값', zorder=5)
        ax_a.set_ylabel("주간 시청 시간 (백만 시간)", fontsize=10, labelpad=8)
        ax_a.set_xlabel("연도 (관측 주차 수 n)", fontsize=10, labelpad=8)
        ax_a.set_ylim(0, max(yearly_agg['mean_hours_m'].max(), yearly_agg['median_hours_m'].max()) * 1.18)

        y_off = yearly_agg['mean_hours_m'].max() * 0.015
        for bar in bars:
            h = bar.get_height()
            ax_a.text(bar.get_x() + bar.get_width() / 2., h + y_off, f'{h:.1f}M',
                      ha='center', va='bottom', fontsize=9.5, fontweight='bold', color=TEXT_COLOR)

        leg_a = ax_a.legend(loc='upper right', frameon=True, facecolor=LEGEND_BG, edgecolor=BORDER_COLOR, fontsize=9)
        for text in leg_a.get_texts():
            text.set_color(TEXT_COLOR)

        n_first = int(yearly_agg.loc[yearly_agg['year'] == first_year, 'week_count'].iloc[0])
        n_last = int(yearly_agg.loc[yearly_agg['year'] == last_year, 'week_count'].iloc[0])
        ax_a.text(0.02, 0.02, f'* 빗금(//)은 부분 연도 ({first_year}: {n_first}주, {last_year}: {n_last}주)',
                  transform=ax_a.transAxes, ha='left', va='bottom', fontsize=8, color=SUB_TEXT, style='italic')

        plt.tight_layout()
        st.pyplot(fig_a, use_container_width=True)
        plt.close(fig_a)

    with col_b:
        st.markdown("### 주요 언어권별 시청 비중 (키워드 분류 추정치)")

        OTHER = '기타·미분류'

        def _kw_regex(words):
            # 단어 경계 일치: 'dp'가 다른 단어 안에서 걸리거나 'dark'가 'Dark Desire'에 걸리는 것을 막는다
            return re.compile(r'(?<![a-z0-9])(?:' + '|'.join(re.escape(w) for w in words) + r')(?![a-z0-9])')

        LANG_RULES = [
            ('한국어', _kw_regex([
                'squid game', 'the glory', 'all of us are dead', 'extraordinary attorney woo',
                'crash landing', 'itaewon', 'vincenzo', 'sweet home', 'hellbound', 'alchemy of souls',
                'king the land', 'queen of tears', 'physical: 100', 'business proposal', 'mask girl',
                'dp', 'my demon', 'doctor cha', 'celebrity', 'daily dose of sunshine', 'gyeongseong'])),
            ('스페인어', _kw_regex([
                'money heist', 'la casa de papel', 'elite', 'berlin', 'who killed sara',
                'pálpito', 'the marked heart', 'fake profile', 'monarca', 'rebelde'])),
            ('일본어', _kw_regex([
                'alice in borderland', 'demon slayer', 'jujutsu kaisen', 'attack on titan',
                'one piece', 'first love', 'sanctuary', 'spy x family'])),
            ('프랑스어', _kw_regex(['lupin', 'class act', 'tapie'])),
            ('독일어', _kw_regex(['1899', 'the empress', 'dear child', 'kleo'])),
        ]

        def detect_language(title):
            tl = str(title).lower().strip()
            for lang, rx in LANG_RULES:
                if rx.search(tl):
                    return lang
            if tl == 'dark':          # 'Dark Desire' 등과 구분하기 위해 정확히 일치할 때만 독일어
                return '독일어'
            return OTHER

        _title_lang = {t: detect_language(t) for t in df_clean['show_title'].unique()}
        df_clean['lang'] = df_clean['show_title'].map(_title_lang)
        lang_sum = df_clean.groupby('lang')['weekly_hours_viewed'].sum()
        lang_pct = (lang_sum / lang_sum.sum()) * 100

        # 가로 바차트용 정렬 (기타·미분류 맨 아래, 주요 언어 점유율순)
        specific_langs = lang_pct.drop(OTHER, errors='ignore').sort_values(ascending=False)
        order_b = ([OTHER] if OTHER in lang_pct.index else []) + list(specific_langs.index[::-1])
        lang_pct_b = lang_pct.loc[order_b]

        fig_b, ax_b = plt.subplots(figsize=(6.5, 5.0))
        apply_active_chart_theme(fig_b, ax_b)

        color_map_b = {
            OTHER: '#777777' if is_dark else '#BDC3C7',
            '프랑스어': '#A0B2C6',
            '일본어': '#7A94B3',
            '독일어': '#5677A0',
            '스페인어': '#2B547E' if not is_dark else '#34495E',
            '한국어': ACCENT_RED
        }
        bar_colors_b = [color_map_b.get(l, '#2B547E') for l in lang_pct_b.index]

        bars_b = ax_b.barh(lang_pct_b.index, lang_pct_b.values, color=bar_colors_b, height=0.56, alpha=0.9)
        ax_b.set_xlabel("Top 10 합산 시청 시간 중 비중 (%)", fontsize=10, labelpad=8)
        ax_b.set_xlim(0, 85)

        for bar in bars_b:
            w = bar.get_width()
            y_pos = bar.get_y() + bar.get_height() / 2.
            if w > 40:
                ax_b.text(w - 2.5, y_pos, f'{w:.1f}%', va='center', ha='right', fontsize=9.2, fontweight='bold', color='white')
            else:
                ax_b.text(w + 1.2, y_pos, f'{w:.1f}%', va='center', ha='left', fontsize=9.2, fontweight='bold', color=TEXT_COLOR)

        plt.tight_layout()
        st.pyplot(fig_b, use_container_width=True)
        plt.close(fig_b)

    st.markdown("#### 🌐 주요 언어권별 누적 시청 시간 및 점유율 현황 (추정)")

    lang_summary_df = pd.DataFrame({
        '언어권 구분': lang_pct.index,
        '누적 시청 시간 (억 시간)': (lang_sum.values / 1e8),
        '글로벌 점유율 (%)': lang_pct.values
    }).sort_values(by='글로벌 점유율 (%)', ascending=False)

    lang_summary_df['누적 시청 시간'] = lang_summary_df['누적 시청 시간 (억 시간)'].apply(lambda x: f"{x:.1f}억 시간")
    lang_summary_df['글로벌 점유율'] = lang_summary_df['글로벌 점유율 (%)'].apply(lambda x: f"{x:.1f}%")

    # 대표 타이틀: 사람이 쓴 문구 대신, 그 언어권으로 분류된 작품 중 누적 시청 상위 3편을 데이터에서 뽑는다
    title_hours = (df_clean.groupby(['lang', 'show_title'])['weekly_hours_viewed'].sum()
                   .reset_index().sort_values('weekly_hours_viewed', ascending=False))
    rep_shows = {
        lang: ", ".join(get_korean_title(t) for t in grp['show_title'].head(3))
        for lang, grp in title_hours.groupby('lang')
    }
    lang_summary_df['누적 시청 상위 3편'] = lang_summary_df['언어권 구분'].map(rep_shows).fillna('-')

    st.dataframe(
        lang_summary_df[['언어권 구분', '누적 시청 시간', '글로벌 점유율', '누적 시청 상위 3편']],
        use_container_width=True,
        hide_index=True
    )

    with st.expander("🔍 언어 분류 검증: 누적 시청 상위 30편의 분류 결과와 '기타·미분류' 상위 15편"):
        st.caption("분류가 의도대로 됐는지 눈으로 확인하는 표입니다. 잘못 들어간 작품이 보이면 키워드 목록(LANG_RULES)을 고치세요.")
        top30 = title_hours.head(30).copy()
        top30['누적 시청(백만 시간)'] = (top30['weekly_hours_viewed'] / 1e6).round(1)
        st.dataframe(top30.rename(columns={'lang': '분류된 언어권', 'show_title': '작품명'})[['작품명', '분류된 언어권', '누적 시청(백만 시간)']],
                     use_container_width=True, hide_index=True)
        other_top = title_hours[title_hours['lang'] == OTHER].head(15).copy()
        other_top['누적 시청(백만 시간)'] = (other_top['weekly_hours_viewed'] / 1e6).round(1)
        st.markdown("**'기타·미분류'로 남은 상위 15편** (실제로는 한국어·스페인어 등일 수 있는 작품이 있는지 확인)")
        st.dataframe(other_top.rename(columns={'show_title': '작품명'})[['작품명', '누적 시청(백만 시간)']],
                     use_container_width=True, hide_index=True)

    ko_pct = float(lang_pct.get('한국어', 0.0))
    es_pct = float(lang_pct.get('스페인어', 0.0))
    other_pct = float(lang_pct.get(OTHER, 0.0))
    ko_hours = float(lang_sum.get('한국어', 0.0)) / 1e8
    st.info(
        f"💡 **언어권 인사이트 (제목 키워드로 분류한 추정치)**: 분류된 언어권 중 **한국어 {ko_pct:.1f}%({ko_hours:.1f}억 시간)**, "
        f"**스페인어 {es_pct:.1f}%** 순으로 비중이 컸습니다. 다만 **{other_pct:.1f}%는 어느 언어권에도 분류하지 못한 작품**이라, "
        "언어 컬럼이 아닌 키워드 목록에 의존한 이 순위는 잠정적입니다. 위 '분류 검증' 표로 확인하세요."
    )