from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import uuid
from app.models.subscription import (
    SubscriptionPlan,
    Subscription,
    Order,
    PlanId,
    PaymentMethod,
    OrderStatus
)
from app.models.user import User, MembershipType
from app.schemas.subscription import (
    SubscriptionPlansResponse,
    SubscriptionPlan as SubscriptionPlanSchema,
    CurrentSubscriptionResponse,
    CreateOrderRequest,
    OrderResponse,
    PaymentCallbackRequest
)
from app.exceptions import NotFoundException, BadRequestException
from app.utils.payment import create_payment_order, verify_payment_callback


def get_subscription_plans(db: Session) -> SubscriptionPlansResponse:
    """Get all subscription plans"""
    plans = db.query(SubscriptionPlan).all()
    
    if not plans:
        # Initialize default plans if none exist
        monthly_plan = SubscriptionPlan(
            id=PlanId.MONTHLY,
            name="月度会员",
            price=39.0,
            period="/月",
            period_subtext=None,
            badge_text=None,
            badge_color=None,
            features=["每日50次处理", "标准处理速度", "标准导出"],
            highlighted=False
        )
        annual_plan = SubscriptionPlan(
            id=PlanId.ANNUAL,
            name="年度会员",
            price=299.0,
            period="/年",
            period_subtext="(平均¥25/月)",
            badge_text="省30%",
            badge_color="primary",
            features=["每日无限使用", "极速处理", "高清导出"],
            highlighted=True
        )
        db.add(monthly_plan)
        db.add(annual_plan)
        db.commit()
        plans = [monthly_plan, annual_plan]
    
    plan_schemas = []
    for plan in plans:
        badge = None
        if plan.badge_text:
            from app.schemas.subscription import PlanBadge, BadgeColor
            badge = PlanBadge(
                text=plan.badge_text,
                color=BadgeColor(plan.badge_color) if plan.badge_color else BadgeColor.PRIMARY
            )
        
        plan_schemas.append(SubscriptionPlanSchema(
            id=PlanId(plan.id.value),
            name=plan.name,
            price=plan.price,
            period=plan.period,
            periodSubtext=plan.period_subtext,
            badge=badge,
            features=plan.features,
            highlighted=plan.highlighted
        ))
    
    return SubscriptionPlansResponse(plans=plan_schemas)


def get_current_subscription(user: User, db: Session) -> CurrentSubscriptionResponse:
    """Get current user subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.is_active == True
    ).first()
    
    if not subscription:
        raise NotFoundException("用户未订阅")
    
    # Get plan manually
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id.value).first()
    if not plan:
        raise NotFoundException("订阅计划不存在")
    
    return CurrentSubscriptionResponse(
        planId=PlanId(subscription.plan_id.value),
        planName=plan.name,
        startDate=subscription.start_date,
        expiryDate=subscription.expiry_date,
        isActive=subscription.is_active,
        autoRenew=subscription.auto_renew
    )


def create_order(
    user: User,
    request: CreateOrderRequest,
    db: Session
) -> OrderResponse:
    """Create subscription order"""
    # Get plan
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == request.planId.value).first()
    if not plan:
        raise NotFoundException("订阅计划不存在")
    
    # Generate order ID
    order_id = f"order_{uuid.uuid4().hex[:12]}"
    
    # Create payment info
    payment_info = create_payment_order(
        order_id,
        plan.price,
        request.paymentMethod,
        f"Lumina AI {plan.name}"
    )
    
    # Create order
    order = Order(
        id=order_id,
        user_id=user.id,
        plan_id=request.planId.value,
        amount=plan.price,
        payment_method=request.paymentMethod.value,
        status=OrderStatus.PENDING,
        payment_info=payment_info,
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return OrderResponse(
        orderId=order.id,
        amount=order.amount,
        paymentInfo=order.payment_info,
        expiresAt=order.expires_at
    )


def handle_payment_callback(
    request: PaymentCallbackRequest,
    db: Session
):
    """Handle payment callback"""
    # Verify payment
    if not verify_payment_callback(
        PaymentMethod(request.paymentMethod),
        request.orderId,
        request.transactionId or "",
        request.amount,
        request.signature
    ):
        raise BadRequestException("支付验证失败")
    
    # Get order
    order = db.query(Order).filter(Order.id == request.orderId).first()
    if not order:
        raise NotFoundException("订单不存在")
    
    if order.status != OrderStatus.PENDING:
        raise BadRequestException("订单状态不正确")
    
    # Update order
    order.status = OrderStatus.PAID
    order.transaction_id = request.transactionId
    order.paid_at = datetime.utcnow()
    db.commit()
    
    # Create or update subscription
    user = db.query(User).filter(User.id == order.user_id).first()
    if not user:
        raise NotFoundException("用户不存在")
    
    # Calculate subscription period
    if order.plan_id == PlanId.MONTHLY.value:
        period_days = 30
    else:  # ANNUAL
        period_days = 365
    
    start_date = datetime.utcnow()
    expiry_date = start_date + timedelta(days=period_days)
    
    # Check if user has active subscription
    existing_subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.is_active == True
    ).first()
    
    if existing_subscription:
        # Extend existing subscription
        if existing_subscription.expiry_date > start_date:
            expiry_date = existing_subscription.expiry_date + timedelta(days=period_days)
        existing_subscription.expiry_date = expiry_date
        existing_subscription.auto_renew = True
    else:
        # Create new subscription
        subscription = Subscription(
            id=f"sub_{uuid.uuid4().hex[:12]}",
            user_id=user.id,
            plan_id=order.plan_id,
            start_date=start_date,
            expiry_date=expiry_date,
            is_active=True,
            auto_renew=True
        )
        db.add(subscription)
        
        # Update user membership
        user.is_pro = True
        if order.plan_id == PlanId.MONTHLY.value:
            user.membership_type = MembershipType.MONTHLY
        else:
            user.membership_type = MembershipType.ANNUAL
        user.membership_expiry = expiry_date
    
    db.commit()

