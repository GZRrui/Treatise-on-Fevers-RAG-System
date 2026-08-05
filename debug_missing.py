"""Debug: find missing article"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'D:/ragpp')

from src.data_loader import DataLoader
loader = DataLoader()
raw = loader.load_raw_data()
clean = loader.clean_data(raw)

raw_ids = set(a['id'] for a in raw)
clean_ids = set(a['id'] for a in clean)
missing_ids = raw_ids - clean_ids
print('Missing IDs:', missing_ids)

for a in raw:
    if a['id'] in missing_ids:
        print('Missing article:')
        print('  ID:', a['id'])
        print('  Chapter:', a['chapter'])
        print('  Text length:', len(a['text']))
        print('  Text preview:', repr(a['text'][:200]))