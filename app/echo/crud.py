from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import User


async def get_operators(session: AsyncSession) -> list[User]:
    stmt = select(User).where(User.is_operator == True)

    result: Result = await session.execute(stmt)
    users = result.scalars().all()

    return list(users)


async def update_user_connect_topic(
    session: AsyncSession, telegram_id: int, topic_id: int
) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    user.user_topic_id = topic_id
    user.connect_operator = True

    await session.commit()
    await session.refresh(user)

    return user
