from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import AI


async def get_ai_use(session: AsyncSession) -> AI:
    stmt = select(AI).where(AI.use == True)

    result: Result = await session.execute(stmt)
    ai = result.scalar_one_or_none()

    if not ai:
        raise "Not use AI"

    return ai
