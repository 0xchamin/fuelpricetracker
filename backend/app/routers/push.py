from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import get_db, settings
from app.models import PushSubscription
from app.auth import require_auth
from pydantic import BaseModel
from pywebpush import webpush, WebPushException
import json

router = APIRouter(prefix="/api/push", tags=["push"])

class SubscriptionData(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    frequency: str = "weekly"

@router.post("/subscribe")
async def subscribe(data: SubscriptionData, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    # Remove old subscription for this user if exists
    await db.execute(delete(PushSubscription).where(PushSubscription.user_id == user_id))
    sub = PushSubscription(user_id=user_id, endpoint=data.endpoint, p256dh=data.p256dh, auth=data.auth, frequency=data.frequency)
    db.add(sub)
    await db.commit()
    return {"status": "subscribed"}

@router.delete("/unsubscribe")
async def unsubscribe(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    await db.execute(delete(PushSubscription).where(PushSubscription.user_id == user_id))
    await db.commit()
    return {"status": "unsubscribed"}

@router.get("/vapid-public-key")
async def get_vapid_key():
    return {"public_key": settings.vapid_public_key}

def send_push(subscription: PushSubscription, message: dict):
    try:
        webpush(
            subscription_info={"endpoint": subscription.endpoint, "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth}},
            data=json.dumps(message),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_claims_email},
        )
    except WebPushException as e:
        print(f"Push failed: {e}")
