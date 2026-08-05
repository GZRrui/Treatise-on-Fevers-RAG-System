"""测试数据加载（无emoji输出）"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, 'D:/ragpp')

print("=== Test 1: Data Loading ===")
from src.data_loader import DataLoader
loader = DataLoader()
raw = loader.load_raw_data()
print(f"Raw data: {len(raw)} articles")
assert len(raw) == 236, f"Expected 236, got {len(raw)}"

clean = loader.clean_data(raw)
print(f"Clean data: {len(clean)} articles")
assert len(clean) == 236, f"Expected 236, got {len(clean)}"

# Check chapter distribution
chapters = {}
for a in clean:
    c = a['chapter']
    chapters[c] = chapters.get(c, 0) + 1
for k, v in sorted(chapters.items()):
    print(f"  - {k}: {v} articles")

print("Data loading: PASSED")
print()

print("=== Test 2: API Key ===")
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('DASHSCOPE_API_KEY', '')
print(f"API Key configured: {bool(key and key != 'your_api_key_here')}")
print(f"API Key length: {len(key)}")
if not key or key == 'your_api_key_here':
    print("WARNING: Please set your DASHSCOPE_API_KEY in .env file")
print()

print("=== Test 3: LlamaIndex Core Modules ===")
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.settings import Settings
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.llms.dashscope import DashScope
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.vector_stores.simple import SimpleVectorStore
print("All core modules importable: PASSED")
print()

print("=== All Tests Passed ===")
print("Next steps:")
print("  1. Set DASHSCOPE_API_KEY in D:/ragpp/.env")
print("  2. Run: D:\\ragpp\\.venv\\Scripts\\python.exe scripts\\build_index.py")