import pandas as pd

def build_weekly_macro_series(df):
    macro = df.groupby('week')['weekly_hours_viewed'].sum().reset_index().sort_values('week').reset_index(drop=True)
    macro['hours_sma_4w'] = macro['weekly_hours_viewed'].rolling(window=4).mean()
    macro['hours_sma_12w'] = macro['weekly_hours_viewed'].rolling(window=12).mean()
    macro['wow_pct_change'] = macro['weekly_hours_viewed'].pct_change() * 100
    return macro