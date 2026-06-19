from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from core.models import Topic, Message


async def delete_old_topics(session: AsyncSession, days: int = 3) -> int:
    cutoff_date = datetime.utcnow() - timedelta(days=days)

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
