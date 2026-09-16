"""
JWT 认证中间件（预留）
用于企业级系统的用户认证
"""

import logging

from fastapi import Request
from fastapi.security import HTTPBearer

logger = logging.getLogger(__name__)

# JWT 安全方案
security = HTTPBearer(auto_error=False)


class JWTAuthMiddleware:
    """
    JWT 认证中间件

    预留功能，用于企业级系统的用户认证和权限控制。
    可根据需要启用。
    """

    def __init__(
        self,
        secret_key: str = "your-secret-key",
        algorithm: str = "HS256",
        excluded_paths: list[str] | None = None,
    ):
        """
        Args:
            secret_key: JWT 密钥
            algorithm: JWT 算法
            excluded_paths: 不需要认证的路径列表
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.excluded_paths = excluded_paths or [
            "/health",
            "/docs",
            "/openapi.json",
        ]

    async def __call__(self, request: Request, call_next):
        """中间件调用"""
        # 检查是否在排除路径中
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # 获取 Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # 可选：允许匿名访问或返回错误
            # return HTTPException(status_code=401, detail="未提供认证令牌")
            return await call_next(request)

        try:
            # 验证 JWT token
            # payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            # request.state.user = payload
            pass

        except Exception as e:
            logger.warning(f"JWT 验证失败: {e}")
            # 可选：返回 401 或允许继续
            # raise HTTPException(status_code=401, detail="无效的认证令牌")

        return await call_next(request)


def create_access_token(data: dict, secret_key: str, algorithm: str = "HS256") -> str:
    """
    创建 JWT token

    预留功能。
    """
    import base64
    import json
    import time

    # 简化的实现，生产环境应使用 PyJWT 库
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": algorithm, "typ": "JWT"}).encode()
    ).decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({**data, "exp": time.time() + 3600}).encode()
    ).decode()
    signature = base64.urlsafe_b64encode(b"signature").decode()

    return f"{header}.{payload}.{signature}"


async def verify_token(token: str, secret_key: str) -> dict | None:
    """
    验证 JWT token

    预留功能。
    """
    # 实现 JWT 验证逻辑
    # 使用 PyJWT 库进行完整实现
    return None
