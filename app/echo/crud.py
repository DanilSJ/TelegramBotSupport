from typing import Optional
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import User, Topic


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
) -> User:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if username and existing_user.username != username:
            existing_user.username = username
            await session.commit()
            await session.refresh(existing_user)
        return existing_user

    user = User(
        telegram_id=telegram_id,
        username=username,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


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


async def create_topic(
    session: AsyncSession,
    name: str,
    topic_id: int,
) -> Topic:
    stmt = select(Topic).where(Topic.topic_id == topic_id)
    result = await session.execute(stmt)
    topic = result.scalar_one_or_none()

    if topic:
        return topic

    topic = Topic(
        name=name,
        topic_id=topic_id,
    )

    session.add(topic)
    await session.commit()
    await session.refresh(topic)

    return topic
