from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Enum as SQLEnum
from datetime import datetime
import enum
from app.database import Base


class PlanId(str, enum.Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class PaymentMethod(str, enum.Enum):
    WECHAT = "wechat"
    ALIPAY = "alipay"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(SQLEnum(PlanId), primary_key=True)
    name = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    period = Column(String(20), nullable=False)  # e.g., "/年"
    period_subtext = Column(String(100), nullable=True)
    badge_text = Column(String(50), nullable=True)
    badge_color = Column(String(20), nullable=True)  # primary, accent
    features = Column(JSON, nullable=False)  # List of strings
    highlighted = Column(Boolean, default=False)

    def __repr__(self):
        return f"<SubscriptionPlan(id={self.id}, name={self.name})>"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    plan_id = Column(SQLEnum(PlanId), nullable=False, index=True)
    start_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan_id={self.plan_id})>"


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    plan_id = Column(SQLEnum(PlanId), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    payment_info = Column(JSON, nullable=True)  # Payment platform specific info
    transaction_id = Column(String(100), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status})>"

