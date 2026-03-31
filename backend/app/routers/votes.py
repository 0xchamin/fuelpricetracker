from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Price, Vote
from app.schemas import VoteSubmission, VoteResponse
from app.auth import require_auth

router = APIRouter(prefix="/api/prices", tags=["votes"])


@router.post("/{price_id}/vote", response_model=VoteResponse)
async def vote_on_price(
    price_id: int,
    submission: VoteSubmission,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = require_auth(request)

    # Check price exists
    price = await db.get(Price, price_id)
    if not price:
        raise HTTPException(status_code=404, detail="Price not found")
    

    # Prevent self-voting
    if price.user_id and price.user_id == user_id:
        raise HTTPException(status_code=403, detail="You cannot vote on your own submission")


    # Check for existing vote by this user
    stmt = select(Vote).where(Vote.price_id == price_id, Vote.user_id == user_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=409, detail="You have already voted on this price")

    # Create vote
    vote = Vote(
        price_id=price_id,
        user_id=user_id,
        vote_type=submission.vote_type,
    )
    db.add(vote)

    # Update upvote count
    if submission.vote_type == "upvote":
        price.upvote_count += 1
        if price.upvote_count >= 5:
            price.is_credible = True

    await db.commit()
    await db.refresh(vote)
    return vote
