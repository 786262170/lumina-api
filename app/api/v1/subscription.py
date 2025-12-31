from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionPlansResponse,
    CurrentSubscriptionResponse,
    CreateOrderRequest,
    OrderResponse,
    PaymentCallbackRequest
)
from app.schemas.common import SuccessResponse
from app.services.subscription_service import (
    get_subscription_plans,
    get_current_subscription,
    create_order,
    handle_payment_callback
)

router = APIRouter()


@router.get("/subscription/plans", response_model=SubscriptionPlansResponse)
async def get_subscription_plans_endpoint(db: Session = Depends(get_db)):
    """获取订阅计划"""
    return get_subscription_plans(db)


@router.get("/subscription/current", response_model=CurrentSubscriptionResponse)
async def get_current_subscription_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前订阅"""
    return get_current_subscription(current_user, db)


@router.post("/subscription/create-order", response_model=OrderResponse)
async def create_subscription_order_endpoint(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建订阅订单"""
    return create_order(current_user, request, db)


@router.post("/subscription/payment-callback", response_model=SuccessResponse)
async def payment_callback_endpoint(
    request: PaymentCallbackRequest,
    db: Session = Depends(get_db)
):
    """支付回调"""
    handle_payment_callback(request, db)
    return SuccessResponse(success=True, message="回调处理成功")
