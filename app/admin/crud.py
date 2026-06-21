from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Result, update
from core.models import AI, User, Message, Start, Phrase


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

    await session.execute(select(AI).where(AI.use == True))
    await session.execute(update(AI).where(AI.use == True).values(use=False))

    ai.use = True

    await session.commit()
    await session.refresh(ai)

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


async def update_ai_message(
    session: AsyncSession,
    message_id: int,
    text: str,
) -> Message | None:
    stmt = select(Message).where(Message.id == message_id)
    result = await session.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        return None

    message.text = text

    await session.commit()
    await session.refresh(message)

    return message


async def delete_message(
    session: AsyncSession,
    message_id: int,
) -> bool:
    stmt = select(Message).where(Message.id == message_id)
    result = await session.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        return False

    await session.delete(message)
    await session.commit()

    return True


async def get_user_messages(
    session: AsyncSession,
    telegram_id: int,
    limit: int = 20,
) -> list[Message]:

    stmt = select(User).where(User.telegram_id == telegram_id)

    result: Result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    stmt = (
        select(Message)
        .where(Message.user_id == user.id)
        .where(Message.topic_id.is_(None))
        .order_by(Message.create_at.desc())
        .limit(limit)
    )

    result: Result = await session.execute(stmt)
    messages = result.scalars().all()

    return list(messages)


async def create_or_update_start(
    session: AsyncSession,
    text: str,
    is_use: bool = False,
) -> Start:
    stmt = select(Start)
    result = await session.execute(stmt)
    start = result.scalar_one_or_none()

    if start:
        start.text = text
        start.is_use = is_use
    else:
        start = Start(
            text=text,
            is_use=is_use,
        )
        session.add(start)

    await session.commit()
    await session.refresh(start)

    return start


async def make_user_operator(
    session: AsyncSession,
    telegram_id: int,
) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    user.is_operator = not user.is_operator

    await session.commit()
    await session.refresh(user)

    return user


async def create_phrase(
    session: AsyncSession,
    text: str,
) -> Phrase:
    phrase = Phrase(
        phrase=text,
    )

    session.add(phrase)
    await session.commit()
    await session.refresh(phrase)

    return phrase


async def delete_phrase(
    session: AsyncSession,
    phrase_id: int,
) -> bool:
    stmt = select(Phrase).where(Phrase.id == phrase_id)
    result = await session.execute(stmt)
    phrase = result.scalar_one_or_none()

    if not phrase:
        return False

    await session.delete(phrase)
    await session.commit()

    return True


async def get_phrases(
    session: AsyncSession,
) -> List[Phrase] | None:
    stmt = select(Phrase)

    result: Result = await session.execute(stmt)
    phrases = result.scalars().all()

    if not phrases:
        return None

    return list(phrases)
