from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PlanId(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class PaymentMethod(str, Enum):
    WECHAT = "wechat"
    ALIPAY = "alipay"


class BadgeColor(str, Enum):
    PRIMARY = "primary"
    ACCENT = "accent"


class PlanBadge(BaseModel):
    text: str = Field(..., example="省30%")
    color: BadgeColor = Field(..., example=BadgeColor.PRIMARY)


class SubscriptionPlan(BaseModel):
    id: PlanId = Field(..., example=PlanId.ANNUAL)
    name: str = Field(..., example="年度会员")
    price: float = Field(..., description="价格（元）", example=299)
    period: str = Field(..., example="/年")
    periodSubtext: Optional[str] = Field(None, example="(平均¥25/月)")
    badge: Optional[PlanBadge] = None
    features: List[str] = Field(..., example=["每日无限使用", "极速处理", "高清导出"])
    highlighted: bool = Field(False, example=True)


class SubscriptionPlansResponse(BaseModel):
    plans: List[SubscriptionPlan]


class CurrentSubscriptionResponse(BaseModel):
    planId: PlanId = Field(..., example=PlanId.ANNUAL)
    planName: str = Field(..., example="年度会员")
    startDate: datetime = Field(..., example="2024-01-01T00:00:00Z")
    expiryDate: datetime = Field(..., example="2025-01-01T00:00:00Z")
    isActive: bool = Field(..., example=True)
    autoRenew: bool = Field(..., example=True)


class CreateOrderRequest(BaseModel):
    planId: PlanId = Field(..., example=PlanId.ANNUAL)
    paymentMethod: PaymentMethod = Field(PaymentMethod.WECHAT, example=PaymentMethod.WECHAT)


class OrderResponse(BaseModel):
    orderId: str = Field(..., example="order_abc123")
    amount: float = Field(..., description="订单金额（元）", example=299)
    paymentInfo: Dict[str, Any] = Field(
        ...,
        description="支付信息（根据支付方式不同）",
        example={
            "qrCode": "https://api.lumina.ai/payment/qr/order_abc123",
            "paymentUrl": "weixin://wxpay/bizpayurl?pr=xxx"
        }
    )
    expiresAt: datetime = Field(..., description="订单过期时间", example="2024-01-15T11:00:00Z")


class PaymentCallbackRequest(BaseModel):
    orderId: str = Field(..., example="order_abc123")
    paymentMethod: PaymentMethod = Field(..., example=PaymentMethod.WECHAT)
    transactionId: Optional[str] = Field(None, example="wx_transaction_123456")
    amount: float = Field(..., example=299)
    signature: Optional[str] = Field(None, description="支付平台签名", example="signature_string")
    timestamp: Optional[int] = Field(None, example=1705315200)

