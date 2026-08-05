"""Debug: find missing article - v2"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'D:/ragpp')

from src.data_loader import DataLoader
loader = DataLoader()
raw = loader.load_raw_data()

# Find the article with ID=176
for a in raw:
    if a['id'] == 176:
        print('Article 176 keys:', list(a.keys()))
        print('Article 176:', a)
        break