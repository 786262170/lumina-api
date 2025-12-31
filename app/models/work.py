from sqlalchemy import Column, String, Integer, DateTime, JSON
from datetime import datetime
from app.database import Base


class Work(Base):
    __tablename__ = "works"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    processed_image_id = Column(String(50), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    category = Column(String(20), nullable=True)  # taobao, douyin, xiaohongshu, amazon, custom
    tags = Column(JSON, nullable=True)  # List of strings
    size = Column(Integer, nullable=False)  # bytes
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Work(id={self.id}, filename={self.filename})>"

