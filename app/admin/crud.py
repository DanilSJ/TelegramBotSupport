from typing import Optional
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from core.models import AI, User


async def create_ai(
    session: AsyncSession,
    model: str,
    base_url: str,
    api_key: str,
    system_prompt: str,
) -> AI:
    ai = AI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        system_prompt=system_prompt,
        use=False,
    )

    session.add(ai)
    await session.commit()
    await session.refresh(ai)

    return ai


async def update_ai_use(
    session: AsyncSession,
    ai_id: int,
) -> AI | None:
    stmt = select(AI).where(AI.id == ai_id)
    result = await session.execute(stmt)
    ai = result.scalar_one_or_none()

    if not ai:
        return None

    ai.use = True

    await session.commit()
    await session.refresh(ai_id)

    return ai


async def block_user(
    session: AsyncSession,
    telegram_id: int,
) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    if user.block:
        user.block = False
    else:
        user.block = True

    await session.commit()
    await session.refresh(user)

    return user
