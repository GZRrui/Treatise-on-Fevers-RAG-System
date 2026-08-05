"""
后端配置
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 基础路径
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"

# API 配置
API_PREFIX = "/api/v1"
API_TITLE = "《伤寒论》RAG 智能问答系统 API"
API_VERSION = "1.0.0"

# CORS 配置
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# 请求限制
MAX_QUERY_LENGTH = 500
DEFAULT_TOP_K = 5
MAX_TOP_K = 20

# 缓存配置
CACHE_TTL = 300  # 5分钟

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = STORAGE_DIR / "logs" / "api.log"