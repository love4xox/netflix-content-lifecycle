"""
verify_numbers.py
리포트에 쓸 숫자를 원본 데이터에서 직접 다시 뽑는 검증 스크립트 (수정 완본)
"""
import os
import numpy as np
import pandas as pd

# ===== CONFIG: 프로젝트 환경에 맞게 자동 경로 탐색 및 설정 =====
# 실제 존재하는 파일 자동 탐색
candidate_paths = [
    ("data/raw/all-weeks-global.tsv", "\t"),
    ("data/all-weeks-global.tsv", "\t"),
    ("../data/raw/all-weeks-global.tsv", "\t"),
    ("data/netflix_tv_non_english.csv", ","),
    ("data/processed/01_weekly_macro_series.csv", ",")
]

PATH, SEP = None, ","
for p, s in candidate_paths:
    if os.path.exists(p):
        PATH, SEP = p, s
        break

if PATH is None:
    # 기본 경로 설정
    PATH = "data/raw/all-weeks-global.tsv"
    SEP = "\t"

COL_DATE = "week"                              # 주차 날짜 컬럼
COL_TITLE = "show_title"                       # 작품명 컬럼
COL_HOURS = "weekly_hours_viewed"              # 주간 시청 시간 컬럼
COL_CUM_WEEKS = "cumulative_weeks_in_top_10"   # 누적 주차 컬럼
COL_SEASON = "season_title"                    # 시즌 단위 작품명 컬럼
COL_LANG = None                                # 원본에 language 컬럼이 없으므로 None 처리
CATEGORY_COL, CATEGORY_VAL = "category", "TV (Non-English)"
CASE_TITLES = ["Squid Game", "Money Heist", "Attorney Woo"]
# ===============================================================


def header(title):
    print(f"\n{'=' * 8} {title} {'=' * 8}")


print(f"▶ 데이터 파일 로드: {PATH} (구분자: {repr(SEP)})")
df = pd.read_csv(PATH, sep=SEP)

if CATEGORY_COL and CATEGORY_COL in df.columns:
    df = df[df[CATEGORY_COL] == CATEGORY_VAL].copy()

df[COL_DATE] = pd.to_datetime(df[COL_DATE])

# ---------- 0. 기본 점검 ----------
header("0. 기본 점검")
print("행 수:", len(df), "| 기간:", df[COL_DATE].min().date(), "~", df[COL_DATE].max().date())
print("결측치:\n", df[[COL_DATE, COL_TITLE, COL_HOURS]].isna().sum())
print("중복 행:", df.duplicated().sum())
weekly = df.groupby(COL_DATE)[COL_HOURS].sum().sort_index()
gaps = weekly.index.to_series().diff().dt.days.dropna()
print("주차 수:", len(weekly), "| 간격이 7일이 아닌 곳:", int((gaps != 7).sum()))

# ---------- 1. 주간 시계열 ----------
header("1. 주간 시청 시간 (백만 시간)")
w = weekly / 1e6
print("최댓값: %.1f (%s)" % (w.max(), w.idxmax().date()))
print("상위 피크 6개 (붙어 있는 주차는 같은 사건으로 볼 것)")
for d, v in w.nlargest(6).items():
    top_show = df[df[COL_DATE] == d].nlargest(1, COL_HOURS)[COL_TITLE].iloc[0]
    print(f"  {d.date()}  {v:7.1f}M  1위 작품: {top_show}")

sma12 = w.rolling(12).mean()
after22 = sma12["2022-01-01":]
if not after22.empty:
    print("12주 이동평균 (2022년 이후): 최소 %.1f (%s) / 최대 %.1f (%s)" % (
        after22.min(), after22.idxmin().date(), after22.max(), after22.idxmax().date()))

print("\n연도별 평균 / 중앙값 / 주 수")
g = w.groupby(w.index.year)
print(pd.DataFrame({"평균": g.mean().round(1), "중앙값": g.median().round(1), "주수": g.size()}))

wow = w.pct_change() * 100
print("\nWoW 최대 증가: %.1f%% (%s) | +80%% 초과 주 수: %d" % (
    wow.max(), wow.idxmax().date(), int((wow > 80).sum())))
print("WoW 최대 하락: %.1f%% (%s)" % (wow.min(), wow.idxmin().date()))

# ---------- 2. 작품 수명 분포 ----------
header("2. 작품 수명 분포")
print("작품 수 (작품명 기준):", df[COL_TITLE].nunique())
if COL_SEASON and COL_SEASON in df.columns:
    print("작품 수 (시즌 단위 기준):", df[COL_SEASON].nunique(), "-> 그래프 03의 666편과 맞는 쪽이 그때 쓴 기준")

by_show = df.groupby(COL_TITLE).agg(total=(COL_HOURS, "sum"), weeks=(COL_DATE, "nunique"))
by_show["weeks_observed"] = by_show["weeks"]

if COL_CUM_WEEKS and COL_CUM_WEEKS in df.columns:
    by_show["weeks_cum"] = df.groupby(COL_TITLE)[COL_CUM_WEEKS].max()
    n_diff = int((by_show["weeks_cum"] != by_show["weeks_observed"]).sum())
    print(f"관측 주차 수와 누적 차트 주차(최댓값)가 다른 작품: {n_diff}편 -> 어느 기준으로 그래프 03을 그렸는지 확인")
    by_show["weeks"] = by_show["weeks_cum"]

labels = ["단기(<=4주)", "중기(5~7주)", "롱런(>=8주)"]
by_show["group"] = pd.cut(by_show["weeks"], [0, 4, 7, np.inf], labels=labels)
print("수명 분류가 안 된 작품:", int(by_show["group"].isna().sum()))
cnt = by_show["group"].value_counts().reindex(labels)
med = by_show.groupby("group", observed=True)["total"].median().div(1e6).round(1)
print(pd.DataFrame({"편수": cnt, "비율%": (cnt / cnt.sum() * 100).round(1), "총시청 중앙값(M)": med}))
print("전체 작품 수:", len(by_show), "(그래프 03의 n 합계 666편과 같은지 확인)")

s = by_show["total"].sort_values(ascending=False)
print("상위 20%% 작품의 누적 시청 비중: %.1f%%" % (s.head(int(len(s) * 0.2)).sum() / s.sum() * 100))
print("상위 10편의 누적 시청 비중: %.1f%%" % (s.head(10).sum() / s.sum() * 100))

# ---------- 3. 언어권 점유율 ----------
header("3. 언어권 점유율")
if COL_LANG and COL_LANG in df.columns:
    ls = df.groupby(COL_LANG, dropna=False)[COL_HOURS].sum().sort_values(ascending=False)
    print((ls / ls.sum() * 100).round(1).head(15))
    print("언어 값 종류 수:", ls.size, "| 언어 결측 행:", int(df[COL_LANG].isna().sum()))
else:
    print("언어 컬럼(language)이 원본에 없음 -> 국가/언어 매핑 데이터셋에서 별도 집계 필요")

# ---------- 4. 감쇄 (최고점 대비 유지율) ----------
header("4. 감쇄: 최고점 대비 유지율")
print("주의: Top 10에서 빠진 주는 데이터에 없으므로 그 이후 감쇄는 보이지 않음")
for kw in CASE_TITLES:
    sub = df[df[COL_TITLE].str.contains(kw, case=False, na=False)]
    if sub.empty and COL_SEASON in df.columns:
        sub = df[df[COL_SEASON].str.contains(kw, case=False, na=False)]
    if sub.empty:
        print(f"\n[{kw}] 일치하는 작품 없음 -> CASE_TITLES 수정")
        continue

    for title, grp in sub.groupby(COL_TITLE):
        grp = grp.sort_values(COL_DATE).reset_index(drop=True)
        peak_i = int(grp[COL_HOURS].idxmax())
        peak_date = grp.loc[peak_i, COL_DATE]
        post = grp.loc[peak_i:].copy()
        post["elapsed_wk"] = ((post[COL_DATE] - peak_date).dt.days / 7).round().astype(int)
        post["retention"] = (post[COL_HOURS] / grp.loc[peak_i, COL_HOURS] * 100).round(0)
        below = post[post["retention"] < 50]
        first_below = int(below["elapsed_wk"].iloc[0]) if len(below) else "없음"
        broken = int((post["elapsed_wk"].diff().dropna() != 1).sum())
        print(f"\n{title} | 피크 주: {peak_date.date()} | 50% 미만 첫 경과 주차: {first_below}")
        print(f"  피크 후 관측 {len(post)}주 | 마지막 관측 경과 주차: {int(post['elapsed_wk'].iloc[-1])} | 끊긴 구간: {broken}곳")
        print("  경과 주차:", post["elapsed_wk"].head(10).tolist())
        print("  날짜:", [d.isoformat() for d in post[COL_DATE].dt.date.head(10)])
        print("  유지율(%):", post["retention"].head(10).tolist())