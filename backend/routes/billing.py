import stripe
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models
from backend.models.schemas import CheckoutRequest
from backend.utils.auth_dep import get_current_user
from backend.utils.plan_guard import require_plan, PDF_LIMITS
from config.settings import get_settings

router = APIRouter()
settings = get_settings()

PRICE_IDS: dict[str, str] = {}


def _get_stripe():
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    stripe.api_key = settings.stripe_secret_key
    # Populate price map at runtime so settings are loaded
    PRICE_IDS["standard"] = settings.stripe_price_standard
    PRICE_IDS["premium"] = settings.stripe_price_premium
    return stripe


@router.post("/create-checkout-session")
async def checkout(
    payload: CheckoutRequest,
    current_user: dict = Depends(get_current_user),
):
    _get_stripe()
    plan = payload.plan
    price_id = PRICE_IDS.get(plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan or price not configured")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.frontend_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.frontend_url}/billing",
        metadata={"user_id": current_user["sub"], "plan": plan},
    )
    return {"url": session.url}


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    if not settings.stripe_secret_key:
        return {"status": "ok"}
    stripe.api_key = settings.stripe_secret_key

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    webhook_secret = settings.stripe_webhook_secret

    if webhook_secret and webhook_secret.startswith("whsec_"):
        # Production: verify Stripe signature
        try:
            event = stripe.Webhook.construct_event(payload, sig, webhook_secret)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    else:
        # Local dev: no signature verification (use Stripe CLI for local testing)
        import json as _json
        try:
            event = _json.loads(payload)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = event["type"]

    if event_type == "checkout.session.completed":
        sess = event["data"]["object"]
        user_id = sess.get("metadata", {}).get("user_id")
        plan = sess.get("metadata", {}).get("plan", "standard")
        subscription_id = sess.get("subscription")
        customer_id = sess.get("customer")
        if user_id:
            sub = db.query(models.Subscription).filter_by(user_id=user_id).first()
            if not sub:
                sub = models.Subscription(
                    user_id=user_id,
                    stripe_customer_id=customer_id,
                    stripe_subscription_id=subscription_id,
                    plan=plan,
                    status="active",
                )
                db.add(sub)
            else:
                sub.stripe_customer_id = customer_id
                sub.stripe_subscription_id = subscription_id
                sub.plan = plan
                sub.status = "active"
            db.commit()

    elif event_type == "customer.subscription.deleted":
        sub_id = event["data"]["object"]["id"]
        sub = db.query(models.Subscription).filter_by(stripe_subscription_id=sub_id).first()
        if sub:
            sub.plan = "free"
            sub.status = "cancelled"
            db.commit()

    elif event_type == "invoice.payment_failed":
        sub_id = event["data"]["object"].get("subscription")
        if sub_id:
            sub = db.query(models.Subscription).filter_by(stripe_subscription_id=sub_id).first()
            if sub:
                sub.status = "past_due"
                db.commit()

    return {"status": "ok"}


@router.get("/portal")
async def billing_portal(
    current_user: dict = Depends(require_plan("standard")),
    db: Session = Depends(get_db),
):
    _get_stripe()
    sub = db.query(models.Subscription).filter_by(user_id=current_user["sub"]).first()
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No billing record found")

    portal = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=f"{settings.frontend_url}/billing",
    )
    return {"url": portal.url}


@router.get("/status")
async def billing_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = db.query(models.Subscription).filter_by(user_id=current_user["sub"]).first()
    plan = sub.plan if sub else "free"
    return {
        "user_id": current_user["sub"],
        "plan": plan,
        "status": sub.status if sub else "active",
        "upload_count": sub.upload_count if sub else 0,
        "upload_limit": PDF_LIMITS[plan],
        "current_period_end": (
            sub.current_period_end.isoformat()
            if sub and sub.current_period_end
            else None
        ),
    }
