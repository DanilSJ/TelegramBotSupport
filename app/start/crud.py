from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import Start


async def get_start_text(session: AsyncSession) -> Start:
    stmt = select(Start).where(Start.is_use == True)

    result: Result = await session.execute(stmt)
    start = result.scalar_one_or_none()

    return start
