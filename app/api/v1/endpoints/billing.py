"""Tax God - Billing & Subscription Endpoints"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.core.config import get_settings
from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionTier

router = APIRouter()
settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY

TRIAL_DAYS = 7


class SubscriptionResponse(BaseModel):
    tier: str
    status: str
    trial_ends_at: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool


class CheckoutResponse(BaseModel):
    checkout_url: str


@router.get("/status", response_model=SubscriptionResponse)
async def get_subscription_status(user: CurrentUser, db: DBSession):
    """Get current user's subscription status."""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    sub = result.scalar_one_or_none()

    if not sub:
        # Auto-create free trial on first check
        sub = Subscription(
            user_id=user.id,
            tier=SubscriptionTier.FREE_TRIAL.value,
            status=SubscriptionStatus.TRIALING.value,
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=TRIAL_DAYS),
        )
        db.add(sub)
        await db.commit()
        await db.refresh(sub)

    # Check if trial expired
    if (
        sub.status == SubscriptionStatus.TRIALING.value
        and sub.trial_ends_at
        and sub.trial_ends_at < datetime.now(timezone.utc)
    ):
        sub.status = SubscriptionStatus.EXPIRED.value
        await db.commit()

    return SubscriptionResponse(
        tier=sub.tier,
        status=sub.status,
        trial_ends_at=sub.trial_ends_at,
        current_period_end=sub.current_period_end,
        cancel_at_period_end=sub.cancel_at_period_end,
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(user: CurrentUser, db: DBSession, request: Request):
    """Create a Stripe checkout session for monthly subscription."""
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PRICE_MONTHLY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe not configured. Set STRIPE_SECRET_KEY and STRIPE_PRICE_MONTHLY in .env",
        )

    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    sub = result.scalar_one_or_none()

    # Get or create Stripe customer
    customer_id = sub.stripe_customer_id if sub else None
    if not customer_id:
        customer = stripe.Customer.create(email=user.email, metadata={"user_id": user.id})
        customer_id = customer.id
        if sub:
            sub.stripe_customer_id = customer_id
            await db.commit()

    base_url = str(request.base_url).rstrip("/")
    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": settings.STRIPE_PRICE_MONTHLY, "quantity": 1}],
        success_url=f"{base_url}/?subscription=success",
        cancel_url=f"{base_url}/?subscription=canceled",
        metadata={"user_id": user.id},
    )

    return CheckoutResponse(checkout_url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: DBSession):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        if user_id:
            result = await db.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            sub = result.scalar_one_or_none()
            if sub:
                sub.tier = SubscriptionTier.PRO.value
                sub.status = SubscriptionStatus.ACTIVE.value
                sub.stripe_customer_id = session.get("customer")
                sub.stripe_subscription_id = session.get("subscription")
                await db.commit()

    elif event["type"] == "customer.subscription.updated":
        stripe_sub = event["data"]["object"]
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_sub["id"]
            )
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = stripe_sub["status"]
            sub.cancel_at_period_end = stripe_sub.get("cancel_at_period_end", False)
            period_end = stripe_sub.get("current_period_end")
            if period_end:
                sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
            await db.commit()

    elif event["type"] == "customer.subscription.deleted":
        stripe_sub = event["data"]["object"]
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_sub["id"]
            )
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = SubscriptionStatus.CANCELED.value
            await db.commit()

    return {"status": "ok"}
