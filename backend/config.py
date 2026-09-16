"""Legacy backend constants backed by the phase-0 environment contract."""

from backend.app.config import get_settings

_settings = get_settings()

API_PREFIX = "/api/v1"
API_TITLE = _settings.app_name
API_VERSION = _settings.app_version
CORS_ORIGINS = _settings.cors_origin_list
MAX_QUERY_LENGTH = 500
DEFAULT_TOP_K = _settings.top_k
MAX_TOP_K = 20
CACHE_TTL = 300
LOG_LEVEL = _settings.log_level
LOG_FILE = _settings.storage_dir / "logs" / "api.log"
