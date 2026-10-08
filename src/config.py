import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_RAW = os.path.join(BASE_DIR, 'data', 'raw')
DATA_INTERIM = os.path.join(BASE_DIR, 'data', 'interim')
DATA_PROCESSED = os.path.join(BASE_DIR, 'data', 'processed')
IMAGES_DIR = os.path.join(BASE_DIR, 'images')

RAW_TSV_PATH = os.path.join(DATA_RAW, 'all-weeks-global.tsv')
INTERIM_CSV_PATH = os.path.join(DATA_INTERIM, 'non_english_tv_clean.csv')