from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=True, index=True)  # Nullable for guest users
    answers = Column(JSON, nullable=False)  # Dict of question_id -> answer_id
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="quiz_sessions")

    def __repr__(self):
        return f"<QuizSession(id={self.id}, user_id={self.user_id})>"

