from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Work(Base):
    __tablename__ = "works"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    processed_image_id = Column(String(50), ForeignKey("images.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    category = Column(String(20), nullable=True)  # taobao, douyin, xiaohongshu, amazon, custom
    tags = Column(JSON, nullable=True)  # List of strings
    size = Column(Integer, nullable=False)  # bytes
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="works")
    processed_image = relationship("Image", backref="works")

    def __repr__(self):
        return f"<Work(id={self.id}, filename={self.filename})>"

