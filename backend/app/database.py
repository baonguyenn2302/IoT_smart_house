from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,           # kiểm tra kết nối trước khi dùng, tránh lỗi "MySQL server has gone away"
    pool_recycle=3600,
    connect_args={"charset": "utf8mb4"},  # để hiển thị đúng tiếng Việt
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency của FastAPI: mỗi request có một session, tự đóng khi xong."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()