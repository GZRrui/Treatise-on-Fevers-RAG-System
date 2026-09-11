import atexit
import os
import shutil
import tempfile
from pathlib import Path

_project_root = Path(__file__).resolve().parents[1]
_test_root = Path(tempfile.mkdtemp(prefix="ragpp-tests-"))
_test_data = _test_root / "data"
_test_data.mkdir()
atexit.register(shutil.rmtree, _test_root, ignore_errors=True)

for _filename in ("shanghanlun_raw.json", "shanghanlun_clean.json"):
    shutil.copy2(_project_root / "data" / _filename, _test_data / _filename)

os.environ["APP_ENV"] = "test"
os.environ["RAG_OFFLINE_MODE"] = "true"
os.environ["DASHSCOPE_API_KEY"] = ""
os.environ["STORAGE_DIR"] = str(_test_root / "storage")
os.environ["DATA_DIR"] = str(_test_data)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_test_root / 'test.db'}"
os.environ["DEBUG"] = "false"
os.environ["CORS_ORIGINS"] = "http://test"
os.environ["JWT_SECRET"] = "test-only-secret-never-use-in-production"
