"""
数据库 ORM 模型
用于查询日志和用户管理（预留）
"""

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from .connection import Base


class QueryLog(Base):
    """
    查询日志表

    记录所有问答查询，用于统计分析和优化。
    """

    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query = Column(Text, nullable=False, comment="用户问题")
    answer = Column(Text, nullable=True, comment="回答内容")
    source_count = Column(Integer, default=0, comment="引用的条文数量")

    # 来源信息
    sources = Column(Text, nullable=True, comment="引用的条文列表（JSON）")

    # 评分信息（预留）
    rating = Column(Integer, nullable=True, comment="用户评分 1-5")
    feedback = Column(Text, nullable=True, comment="用户反馈")

    # 元信息
    user_id = Column(String(100), nullable=True, index=True, comment="用户ID")
    session_id = Column(String(100), nullable=True, index=True, comment="会话ID")
    client_ip = Column(String(50), nullable=True, comment="客户端IP")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<QueryLog(id={self.id}, query='{self.query[:50]}...')>"


class User(Base):
    """
    用户表（预留）

    用于企业级系统的用户管理。
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # 权限
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # 用户配置
    api_key = Column(String(100), nullable=True, unique=True)
    daily_quota = Column(Integer, default=100)  # 每日配额

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class UsageLog(Base):
    """
    使用量日志表（预留）

    用于追踪 API 调用量和资源消耗。
    """

    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), nullable=True, index=True)

    # 调用信息
    endpoint = Column(String(100), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)

    # 资源消耗
    tokens_used = Column(Integer, default=0)
    embedding_calls = Column(Integer, default=0)

    # 性能
    duration_ms = Column(Float, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now(), index=True)

    def __repr__(self):
        return f"<UsageLog(id={self.id}, endpoint='{self.endpoint}')>"