from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean, Enum as SQLEnum
from datetime import datetime
import enum
from app.database import Base


class ImageFormat(str, enum.Enum):
    JPG = "jpg"
    PNG = "png"
    WEBP = "webp"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Image(Base):
    __tablename__ = "images"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    thumbnail = Column(String(500), nullable=True)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    size = Column(Integer, nullable=False)  # bytes
    format = Column(SQLEnum(ImageFormat), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Image(id={self.id}, filename={self.filename})>"


class ProcessTask(Base):
    __tablename__ = "process_tasks"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    image_id = Column(String(50), nullable=False, index=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    progress = Column(Integer, default=0)  # 0-100
    operations = Column(JSON, nullable=False)  # List of ImageOperation
    result_image_id = Column(String(50), nullable=True, index=True)
    output_size = Column(String(20), nullable=True)  # e.g., "2000x2000"
    quality = Column(Integer, default=85)
    edge_smoothing = Column(Boolean, default=True)
    scene_type = Column(String(20), nullable=True)
    error_message = Column(String(500), nullable=True)
    processing_time = Column(Integer, nullable=True)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ProcessTask(id={self.id}, status={self.status})>"

