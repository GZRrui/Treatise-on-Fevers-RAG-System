"""
请求日志中间件
记录所有请求的详细信息
"""

from fastapi import Request
from datetime import datetime
import logging
import time
import json

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """请求日志中间件"""

    def __init__(self, log_body: bool = False):
        """
        Args:
            log_body: 是否记录请求体（可能包含敏感信息）
        """
        self.log_body = log_body

    async def __call__(self, request: Request, call_next):
        """中间件调用"""
        start_time = time.time()
        request_id = id(request)

        # 记录请求开始
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", ""),
        }

        logger.info(f"请求开始: {json.dumps(log_data, ensure_ascii=False)}")

        # 处理请求
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # 记录响应
            log_data.update({
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            })

            if response.status_code >= 400:
                logger.warning(f"请求异常: {json.dumps(log_data, ensure_ascii=False)}")
            else:
                logger.info(f"请求完成: {json.dumps(log_data, ensure_ascii=False)}")

            return response

        except Exception as e:
            duration = time.time() - start_time
            log_data.update({
                "error": str(e),
                "duration_ms": round(duration * 1000, 2),
            })
            logger.error(f"请求失败: {json.dumps(log_data, ensure_ascii=False)}")
            raise