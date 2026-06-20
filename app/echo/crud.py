from typing import Optional
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from core.models import User, Topic, Message, Phrase


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


async def update_user_disconnect_topic(
    session: AsyncSession, user_id: int
) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    user.user_topic_id = None
    user.connect_operator = False

    await session.commit()
    await session.refresh(user)

    return user


async def create_topic(
    session: AsyncSession,
    name: str,
    topic_id: int,
    user_id: int,
) -> Topic:
    stmt = select(Topic).where(Topic.topic_id == topic_id)
    result = await session.execute(stmt)
    topic = result.scalar_one_or_none()

    if topic:
        return topic

    topic = Topic(
        name=name,
        topic_id=topic_id,
        user_id=user_id,
    )

    session.add(topic)
    await session.commit()
    await session.refresh(topic)

    return topic


async def create_message(
    session: AsyncSession,
    user_id: int,
    id_message: int,
    message: str,
    topic_id: int | None = None,
    ai_message: str | None = None,
) -> Message:
    message_obj = Message(
        id_message=id_message,
        message=message,
        ai_message=ai_message,
        topic_id=topic_id,
        user_id=user_id,
    )

    session.add(message_obj)
    await session.commit()
    await session.refresh(message_obj)

    return message_obj


async def get_user_messages(
    session: AsyncSession,
    user_id: int,
    limit: int = 20,
) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.user_id == user_id)
        .where(Message.topic_id.is_(None))
        .order_by(Message.create_at.desc())
        .limit(limit)
    )

    result: Result = await session.execute(stmt)
    messages = result.scalars().all()

    return list(messages)


async def get_topics(session: AsyncSession) -> list[Topic]:
    stmt = select(Topic)

    result: Result = await session.execute(stmt)
    topics = result.scalars().all()

    return list(topics)


async def get_user(session: AsyncSession, user_id: int) -> User:
    stmt = select(User).where(User.id == user_id)

    result: Result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    return user


async def get_phrases(session: AsyncSession) -> list[str]:
    stmt = select(func.lower(Phrase.phrase))

    result: Result = await session.execute(stmt)
    phrases = result.scalars().all()

    return list(phrases)
