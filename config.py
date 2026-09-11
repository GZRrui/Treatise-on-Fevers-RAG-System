"""Legacy configuration constants backed by the phase-0 environment contract."""

from pathlib import Path

from backend.app.config import get_settings


_settings = get_settings()

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = _settings.storage_dir
DATA_DIR = _settings.data_dir
SRC_DIR = BASE_DIR / "src"
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

DASHSCOPE_API_KEY = _settings.dashscope_api_key
DASHSCOPE_API_BASE = _settings.dashscope_api_base
OFFLINE_MODE = _settings.rag_offline_mode
EMBEDDING_MODEL = _settings.embedding_model
EMBEDDING_DIM = _settings.embedding_dim
LLM_MODEL = _settings.llm_model
LLM_TEMPERATURE = _settings.llm_temperature
LLM_MAX_TOKENS = _settings.llm_max_tokens
TOP_K = _settings.top_k
SIMILARITY_THRESHOLD = _settings.similarity_threshold
DATABASE_URL = _settings.resolved_database_url
VECTOR_STORE_PATH = str(_settings.resolved_vector_store_path)
HOST = _settings.host
PORT = _settings.port
DEBUG = _settings.debug
JWT_SECRET = _settings.jwt_secret
JWT_ALGORITHM = _settings.jwt_algorithm
JWT_EXPIRATION_HOURS = _settings.jwt_expiration_hours
RATE_LIMIT_REQUESTS = _settings.rate_limit_requests
RATE_LIMIT_WINDOW = _settings.rate_limit_window
RAW_DATA_PATH = DATA_DIR / "shanghanlun_raw.json"
CLEAN_DATA_PATH = DATA_DIR / "shanghanlun_clean.json"
LOG_LEVEL = _settings.log_level
LOG_FILE = STORAGE_DIR / "logs" / "app.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
