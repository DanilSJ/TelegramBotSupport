from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from core.models import Topic, Message
from datetime import datetime, timezone, timedelta

MSK = timezone(timedelta(hours=3))


async def delete_old_topics(session: AsyncSession, days: int = 3) -> int:
    """Удаляет старые топики (старше days дней)"""
    cutoff_date = datetime.now(MSK) - timedelta(days=days)

    subquery = (
        select(Message.topic_id, func.max(Message.create_at).label("last_message_date"))
        .group_by(Message.topic_id)
        .subquery()
    )

    stmt = (
        select(Topic)
        .outerjoin(subquery, Topic.id == subquery.c.topic_id)
        .where(
            (subquery.c.last_message_date < cutoff_date)
            | (subquery.c.last_message_date.is_(None))
        )
    )

    result = await session.execute(stmt)
    topics_to_delete = result.scalars().all()

    for topic in topics_to_delete:
        await session.delete(topic)

    await session.commit()
    return len(topics_to_delete)


async def delete_closed_topics(session: AsyncSession) -> int:
    """Удаляет закрытые топики, которые были закрыты более 30 минут назад"""
    thirty_minutes_ago = datetime.now(MSK) - timedelta(minutes=30)

    # Находим топики, которые закрыты и были закрыты более 30 минут назад
    stmt = select(Topic).where(
        and_(Topic.is_closed == True, Topic.closed_at <= thirty_minutes_ago)
    )

    result = await session.execute(stmt)
    topics_to_delete = result.scalars().all()

    for topic in topics_to_delete:
        await session.delete(topic)

    await session.commit()
    return len(topics_to_delete)


async def check_and_delete_closed_topics(session: AsyncSession) -> dict:
    """Проверяет все топики и удаляет закрытые через 30 минут"""
    # Удаляем закрытые топики (старше 30 минут)
    deleted_count = await delete_closed_topics(session)

    return {"deleted_closed": deleted_count}
