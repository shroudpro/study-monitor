"""
SQLite 数据库连接与会话管理

NOTE: 使用 SQLAlchemy 管理数据库连接，确保线程安全和连接复用。
SQLite 的 check_same_thread=False 允许 FastAPI 的异步环境使用。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def getDb():
    """
    FastAPI 依赖注入：获取数据库会话，请求结束后自动关闭
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initDb():
    """
    初始化数据库表结构（首次运行时自动创建）
    """
    from app.model.models import BehaviorLog, BehaviorRule, SemanticLog, StudySession, NlRuleParseLog  # noqa: F401
    Base.metadata.create_all(bind=engine)
