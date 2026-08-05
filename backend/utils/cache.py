"""
缓存工具（预留）
简单的内存缓存，生产环境建议使用 Redis
"""

from typing import Any, Optional
import time
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    """
    简单内存缓存

    预留功能，用于缓存频繁访问的数据。
    生产环境建议使用 Redis。
    """

    def __init__(self, default_ttl: int = 300):
        """
        Args:
            default_ttl: 默认过期时间（秒）
        """
        self.default_ttl = default_ttl
        self._cache = {}
        self._expiry = {}

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在或已过期返回 None
        """
        # 检查是否存在
        if key not in self._cache:
            return None

        # 检查是否过期
        if key in self._expiry and time.time() > self._expiry[key]:
            del self._cache[key]
            del self._expiry[key]
            return None

        return self._cache[key]

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 使用默认值
        """
        self._cache[key] = value
        self._expiry[key] = time.time() + (ttl or self.default_ttl)

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]
        return True

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._expiry.clear()

    def keys(self) -> list:
        """获取所有缓存键"""
        return list(self._cache.keys())

    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


# 全局缓存实例
_cache = SimpleCache(default_ttl=300)


def get_cache() -> SimpleCache:
    """获取全局缓存实例"""
    return _cache