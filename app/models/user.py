from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.mysql import BIGINT
from datetime import datetime
import enum
from app.database import Base


class MembershipType(str, enum.Enum):
    FREE = "free"
    MONTHLY = "monthly"
    ANNUAL = "annual"
    ENTERPRISE = "enterprise"


class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=True)
    nickname = Column(String(50), nullable=True)
    avatar = Column(String(500), nullable=True)
    is_pro = Column(Boolean, default=False)
    membership_type = Column(SQLEnum(MembershipType), default=MembershipType.FREE)
    membership_expiry = Column(DateTime, nullable=True)
    wechat_openid = Column(String(100), unique=True, nullable=True, index=True)
    is_guest = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, phone={self.phone_number})>"


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    phone_number = Column(String(20), index=True, nullable=False)
    code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used = Column(Boolean, default=False)

    def __repr__(self):
        return f"<VerificationCode(phone={self.phone_number}, code={self.code})>"

