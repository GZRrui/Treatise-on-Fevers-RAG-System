"""
统一配置管理 - 所有可配置参数集中在此文件
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# ============ 基础路径 ============
BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
DATA_DIR = BASE_DIR / "data"
SRC_DIR = BASE_DIR / "src"
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"

# 确保目录存在
STORAGE_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ============ DashScope 配置 ============
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
OFFLINE_MODE = os.getenv("RAG_OFFLINE_MODE", "false").lower() in {"1", "true", "yes", "on"}
if not DASHSCOPE_API_KEY and not OFFLINE_MODE:
    raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量")

DASHSCOPE_API_BASE = os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# ============ Embedding 配置 ============
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

# ============ LLM 配置 ============
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

# ============ 检索配置 ============
TOP_K = int(os.getenv("TOP_K", "5"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))

# ============ 数据库配置 ============
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{STORAGE_DIR}/rag_system.db")

# ============ 向量存储配置 ============
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", str(STORAGE_DIR / "vector_store.json"))

# ============ FastAPI 配置 ============
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# ============ JWT 配置（预留）============
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# ============ 限流配置（预留）============
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# ============ 数据文件路径 ============
RAW_DATA_PATH = DATA_DIR / "shanghanlun_raw.json"
CLEAN_DATA_PATH = DATA_DIR / "shanghanlun_clean.json"

# ============ 日志配置 ============
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = STORAGE_DIR / "logs" / "app.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
