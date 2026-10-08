import pandas as pd
from .config import RAW_TSV_PATH, INTERIM_CSV_PATH

def load_and_clean_non_english_tv():
    df_raw = pd.read_csv(RAW_TSV_PATH, sep='\t')
    df_non_eng = df_raw[df_raw['category'] == 'TV (Non-English)'].copy()
    df_non_eng['week'] = pd.to_datetime(df_non_eng['week'])
    df_non_eng = df_non_eng.sort_values(by=['week', 'weekly_rank']).reset_index(drop=True)
    df_non_eng.to_csv(INTERIM_CSV_PATH, index=False)
    return df_non_eng