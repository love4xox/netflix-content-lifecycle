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
    /* 1. 상단 Streamlit 헤더 흰 띠 완전 제거 */
    header[data-testid="stHeader"] {{
        background-color: {HEADER_BG} !important;
    }}
    
    /* 2. 전체 배경 및 본문 */
    .stApp {{
        background-color: {APP_BG};
        color: {TEXT_COLOR};
        font-family: -apple-system, BlinkMacSystemFont, "Malgun Gothic", "Pretendard", sans-serif;
    }}
    
    /* 3. 사이드바 라디오 버튼 텍스트 또렷하게 */
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

    /* 4. 타이틀 및 헤더 */
    h1, h2, h3, h4 {{
        color: {TEXT_COLOR} !important;
        font-weight: 700 !important;
    }}

    /* 5. 지표 메트릭 카드 */
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

    /* 6. 탭 메뉴 글씨 선명화 */
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

    /* 7. 알림/인사이트 카드 */
    .stAlert {{
        background-color: {CARD_BG} !important;
        border: 1px solid {BORDER_COLOR} !important;
        border-radius: 8px !important;
        color: {TEXT_COLOR} !important;
    }}

    /* 8. 데이터프레임 */
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
    t_str = str(title).strip()
    if t_str in TITLE_KOR_MAP:
        return f"{TITLE_KOR_MAP[t_str]} ({t_str})"
    for k, v in TITLE_KOR_MAP.items():
        if k.lower() in t_str.lower():
            return f"{v} ({t_str})"
    return t_str

# ---------------------------------------------------------
# [4] 데이터 로드 (캐싱)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    macro = pd.read_csv('data/processed/01_weekly_macro_series.csv')
    macro['week'] = pd.to_datetime(macro['week'])
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
st.markdown(f"<p style='color:{SUB_TEXT}; margin-top:-8px; margin-bottom:25px; font-size:1.05rem;'>글로벌 Top 10 시청 데이터를 기반으로 거시 시계열 트렌드, 주간 변동성 충격, 작품 수명 분포, 메가히트작 반감기를 분석합니다.</p>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
total_weeks = len(weekly_macro)
total_shows = len(show_summary)
peak_macro_hours = weekly_macro['weekly_hours_viewed'].max() / 1e8
avg_weekly_hours = weekly_macro['weekly_hours_viewed'].mean() / 1e8

col1.metric("총 분석 주차", f"{total_weeks} 주", "2021 ~ 2026")
col2.metric("총 분석 타이틀", f"{total_shows:,} 편", "비영어권 Top 10")
col3.metric("역대 최고 주간 시청량", f"{peak_macro_hours:.1f}억 시간", "오징어 게임 방영기")
col4.metric("주간 평균 기본 시청량", f"{avg_weekly_hours:.1f}억 시간", "글로벌 기본 체력")

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
# TAB 1: 주간 거시 트렌드 & 변동성 분포 (누락 차트 추가 완료)
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
    
    ax.set_title("넷플릭스 비영어권 TV 주간 총 시청 시간 및 3-Line 이동평균 트렌드", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("기간", fontsize=11, labelpad=8)
    ax.set_ylabel("시청 시간 (백만 시간)", fontsize=11, labelpad=8)
    leg = ax.legend(loc='upper right', frameon=True, facecolor=LEGEND_BG, edgecolor=BORDER_COLOR, fontsize=10)
    for text in leg.get_texts():
        text.set_color(TEXT_COLOR)
    
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

    # 누락되었던 2번 그래프: 주간 증감률(WoW) 변동성 분포 히스토그램
    st.markdown("### 2. 주간 증감률(WoW %) 변동성 및 충격 분포 (Volatilty & Skewness)")
    
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

    st.markdown("#### 📊 연도별 거시 시청 실적 및 성장률 요약")
    macro_table = weekly_macro.groupby('year').agg(
        총주차=('week', 'count'),
        연간총시청=('weekly_hours_viewed', 'sum'),
        주간평균시청=('weekly_hours_viewed', 'mean'),
        주간최고기록=('weekly_hours_viewed', 'max'),
        주간최저기록=('weekly_hours_viewed', 'min'),
        평균변동률=('wow_pct_change', lambda x: x.abs().mean())
    ).reset_index()

    macro_table['연도'] = macro_table['year'].apply(lambda x: f"{x}년")
    macro_table['연간 총 시청 시간'] = macro_table['연간총시청'].apply(lambda x: f"{x/1e8:.1f}억 시간")
    macro_table['주간 평균 시청 시간'] = macro_table['주간평균시청'].apply(lambda x: f"{x/1e8:.2f}억 시간")
    macro_table['주간 최고 시청 기록'] = macro_table['주간최고기록'].apply(lambda x: f"{x/1e8:.2f}억 시간")
    macro_table['주간 최저 시청 기록'] = macro_table['주간최저기록'].apply(lambda x: f"{x/1e8:.2f}억 시간")
    macro_table['평균 주간 변동폭(WoW)'] = macro_table['평균변동률'].apply(lambda x: f"±{x:.1f}%")

    st.dataframe(
        macro_table[['연도', '총주차', '연간 총 시청 시간', '주간 평균 시청 시간', '주간 최고 시청 기록', '주간 최저 시청 기록', '평균 주간 변동폭(WoW)']],
        use_container_width=True,
        hide_index=True
    )

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.info("💡 **안정화 추세**: 2021년 9월 '오징어 게임' 당시 역대 최고 주간 5.7억 시간을 기록한 이후, 2022년부터 2026년까지 분기 추세선(12주 SMA)이 1.8억~2.2억 시간대를 안정적으로 방어하고 있습니다.")
    with col_t2:
        st.info("💡 **변동성 특성**: 주간 증감률(WoW)은 대형 신작 공개 여부에 따라 매주 평균 ±10~15% 수준의 변동폭을 보이며, 초대형 히트작 론칭 시 양의 극단값(Outlier)이 발생하는 우측 꼬리 분포(Positive Skewness)를 나타냅니다.")

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
    ax.set_ylabel("총 누적 시청 시간 (로그 스케일)", fontsize=11, labelpad=8)
    
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    
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

    st.success("📌 **작품 해설**: 장기 차트인 1위는 32주간 머문 **오징어 게임**, 2위와 3위는 중남미의 전설적 텔레노벨라 **베티는 못말려**와 **여인의 향기**, 4위와 5위는 글로벌 K-드라마 열풍을 주도한 **환혼**과 **이상한 변호사 우영우**입니다.")

# ---------------------------------------------------------
# TAB 3: 메가히트작 반감기(Half-Life) 비교
# ---------------------------------------------------------
with tab3:
    st.markdown("### 최고점(Peak) 이후 감쇄 곡선 및 50% 반감기 비교")
    
    all_decay_shows = list(df_decay_post['show_title'].unique())
    show_kor_dict = {
        'Squid Game': '오징어 게임',
        'Money Heist': '종이의 집',
        'Extraordinary Attorney Woo': '이상한 변호사 우영우'
    }
    
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
        
        for show in selected_shows:
            sub = df_decay_post[df_decay_post['show_title'] == show]
            kor_label = show_kor_dict.get(show, show)
            ax.plot(sub['weeks_since_peak'], sub['normalized_pct'], 
                    label=kor_label, color=color_map.get(show, '#AAAAAA'), marker='o', linewidth=2.2)
        
        threshold_color = '#FFFFFF' if is_dark else '#000000'
        ax.axhline(50, color=threshold_color, linestyle='--', linewidth=1.2, label='반감기 기준선 (50%)')
        ax.set_title("최고점(Week 0) 이후 주차별 시청 시간 유지율 (%)", fontsize=13, fontweight='bold', pad=12)
        ax.set_xlabel("피크 이후 경과 주차 (Week)", fontsize=11, labelpad=8)
        ax.set_ylabel("최고 시청 시간 대비 유지율 (%)", fontsize=11, labelpad=8)
        ax.set_xlim(-0.5, 15)
        ax.set_ylim(0, 105)
        leg = ax.legend(loc='upper right', frameon=True, facecolor=LEGEND_BG, edgecolor=BORDER_COLOR)
        for text in leg.get_texts():
            text.set_color(TEXT_COLOR)
        
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)

        st.markdown("#### ⏱️ 주요 메가히트작 반감기(Half-Life) 도달 현황")
        decay_summary_list = []
        for show in selected_shows:
            sub = df_decay_post[df_decay_post['show_title'] == show]
            peak_val = sub[sub['weeks_since_peak'] == 0]['weekly_hours_viewed'].values[0] if not sub[sub['weeks_since_peak'] == 0].empty else 0
            
            below_50 = sub[sub['normalized_pct'] <= 50]
            half_life_week = f"{below_50['weeks_since_peak'].min()}주 차" if not below_50.empty else "15주 이상 유지"

            decay_summary_list.append({
                '작품명': show_kor_dict.get(show, show),
                '원제': show,
                '최고 주간 시청 시간': f"{peak_val / 1e8:.2f}억 시간",
                '50% 반감기 도달 시점': half_life_week,
                '감쇄 패턴 유형': '급격한 지수 감쇄 (폭발형)' if 'Money' in show or 'Squid' in show else '완만한 롱테일 (입소문형)'
            })
        
        st.dataframe(pd.DataFrame(decay_summary_list), use_container_width=True, hide_index=True)
        st.info("💡 **인사이트 요약**: 대형 기대작은 방영 1~2주 차에 최고 시청 시간을 기록한 뒤 **2~3주 이내에 50% 반감기에 도달**합니다. 반면 한국형 스토리텔링작(예: 이상한 변호사 우영우)은 후반부 회차가 순차 공개되면서 완만한 곡선을 그리며 생명력을 오래 유지합니다.")

    else:
        st.warning("분석할 작품을 1개 이상 선택해 주세요.")

# ---------------------------------------------------------
# TAB 4: 연도별 및 언어권별 점유율
# ---------------------------------------------------------
with tab4:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("### 연도별 주간 평균 시청 시간")
        yearly_avg = weekly_macro.groupby('year')['weekly_hours_viewed'].mean() / 1e6
        years = [f"{y}년" for y in yearly_avg.index]
        
        fig_a, ax_a = plt.subplots(figsize=(6.2, 4.8))
        apply_active_chart_theme(fig_a, ax_a)
        
        palette_bar = ['#4A90E2', '#2ECC71', '#F5A623', '#E50914', '#9B59B6', '#888888']
        bars = ax_a.bar(years, yearly_avg.values, color=palette_bar[:len(years)], width=0.52, alpha=0.9)
        ax_a.set_ylabel("평균 시청 시간 (백만 시간)", fontsize=10, labelpad=8)
        ax_a.set_xlabel("연도", fontsize=10, labelpad=8)
        
        for bar in bars:
            h = bar.get_height()
            ax_a.text(bar.get_x() + bar.get_width() / 2., h + 2.5, f'{h:.1f}M', 
                      ha='center', va='bottom', fontsize=9, fontweight='bold', color=TEXT_COLOR)
        
        plt.tight_layout()
        st.pyplot(fig_a, use_container_width=True)
        
    with col_b:
        st.markdown("### 주요 언어권별 글로벌 시청 비중")
        
        def detect_language(title):
            tl = str(title).lower()
            korean_kw = [
                'squid game', 'glory', 'all of us are dead', 'extraordinary attorney woo', 
                'crash landing', 'itaewon', 'vincenzo', 'sweet home', 'hellbound', 'alchemy of souls',
                'king the land', 'queen of tears', 'physical: 100', 'business proposal', 'mask girl',
                'dp', 'my demon', 'doctor cha', 'celebrity', 'daily dose of sunshine', 'gyeongseong'
            ]
            spanish_kw = [
                'money heist', 'la casa de papel', 'elite', 'berlin', 'who killed sara', 
                'pálpito', 'the marked heart', 'fake profile', 'monarca', 'rebelde', 'betty'
            ]
            japanese_kw = [
                'alice in borderland', 'demon slayer', 'jujutsu kaisen', 'attack on titan', 
                'one piece', 'first love', 'sanctuary', 'spy x family'
            ]
            french_kw = ['lupin', 'class act', 'tapie']
            german_kw = ['dark', '1899', 'the empress', 'dear child', 'kleo']

            for k in korean_kw:
                if k in tl: return '한국어 (K-드라마)'
            for k in spanish_kw:
                if k in tl: return '스페인어'
            for k in japanese_kw:
                if k in tl: return '일본어'
            for k in french_kw:
                if k in tl: return '프랑스어'
            for k in german_kw:
                if k in tl: return '독일어'
            return '기타 언어권'
            
        df_clean['lang'] = df_clean['show_title'].apply(detect_language)
        lang_share = df_clean.groupby('lang')['weekly_hours_viewed'].sum().sort_values(ascending=False)
        
        fig_b, ax_b = plt.subplots(figsize=(6.2, 4.8))
        fig_b.patch.set_facecolor(CHART_BG)
        ax_b.set_facecolor(CHART_BG)
        
        colors_pie = ['#E50914', '#F5A623', '#4A90E2', '#2ECC71', '#9B59B6', '#555555']
        wedge_edge = '#141414' if is_dark else '#FFFFFF'
        wedges, texts, autotexts = ax_b.pie(
            lang_share.values, 
            autopct=lambda p: f'{p:.1f}%' if p > 3 else '',
            startangle=140, 
            colors=colors_pie[:len(lang_share)],
            wedgeprops={'edgecolor': wedge_edge, 'linewidth': 1.5},
            pctdistance=0.75
        )
        for at in autotexts:
            at.set_fontsize(9.5)
            at.set_color('#FFFFFF')
            at.set_weight('bold')

        leg_b = ax_b.legend(
            wedges, 
            [f"{label} ({val/lang_share.sum()*100:.1f}%)" for label, val in zip(lang_share.index, lang_share.values)],
            loc="center left", 
            bbox_to_anchor=(0.92, 0.5), 
            frameon=True, 
            facecolor=LEGEND_BG,
            edgecolor=BORDER_COLOR,
            fontsize=9
        )
        for text in leg_b.get_texts():
            text.set_color(TEXT_COLOR)
        
        plt.tight_layout()
        st.pyplot(fig_b, use_container_width=True)

    st.markdown("#### 🌐 주요 언어권별 누적 시청 시간 및 점유율 현황")
    
    total_non_eng = lang_share.sum()
    lang_summary_df = pd.DataFrame({
        '언어권 구분': lang_share.index,
        '누적 시청 시간 (억 시간)': lang_share.values / 1e8,
        '글로벌 점유율 (%)': (lang_share.values / total_non_eng) * 100
    })
    
    lang_summary_df['누적 시청 시간'] = lang_summary_df['누적 시청 시간 (억 시간)'].apply(lambda x: f"{x:.1f}억 시간")
    lang_summary_df['글로벌 점유율'] = lang_summary_df['글로벌 점유율 (%)'].apply(lambda x: f"{x:.1f}%")
    
    rep_shows = {
        '한국어 (K-드라마)': '오징어 게임, 더 글로리, 이상한 변호사 우영우, 눈물의 여왕',
        '스페인어': '종이의 집, 엘리트들, 베를린, 베티는 못말려',
        '일본어': '아리스 인 보더랜드, 귀멸의 칼날, 원피스, 주술회전',
        '독일어': '다크 (Dark), 1899, 황후 엘리자베트',
        '프랑스어': '뤼팽 (Lupin), 타피에',
        '기타 언어권': '중남미 텔레노벨라, 북유럽 스릴러, 기타 로컬 오리지널'
    }
    lang_summary_df['주요 대표 타이틀'] = lang_summary_df['언어권 구분'].map(rep_shows).fillna('-')

    st.dataframe(
        lang_summary_df[['언어권 구분', '누적 시청 시간', '글로벌 점유율', '주요 대표 타이틀']],
        use_container_width=True,
        hide_index=True
    )

    st.info("💡 **언어권 인사이트**: 비영어권 TV 콘텐츠 중 **한국어(K-드라마)**와 **스페인어** 콘텐츠가 전체 시청 시간의 독보적인 비중을 차지하며 쌍두마차 체제를 구축하고 있습니다. 특히 한국 드라마는 아시아뿐만 아니라 미주, 유럽 등 전 대륙에 걸쳐 가장 폭넓은 시청층을 확보하고 있습니다.")