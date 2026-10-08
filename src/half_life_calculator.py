import pandas as pd

def calculate_normalized_decay(df, target_shows):
    decay_records = []
    for show in target_shows:
        sub = df[df['show_title'] == show].sort_values('week').reset_index(drop=True)
        peak_val = sub['weekly_hours_viewed'].max()
        sub['normalized_pct'] = (sub['weekly_hours_viewed'] / peak_val) * 100
        peak_idx = sub['normalized_pct'].idxmax()
        sub['relative_week_from_peak'] = range(-peak_idx, len(sub) - peak_idx)
        post_peak = sub[sub['relative_week_from_peak'] >= 0].copy()
        post_peak['weeks_since_peak'] = post_peak['relative_week_from_peak']
        decay_records.append(post_peak)
    return pd.concat(decay_records, ignore_index=True)