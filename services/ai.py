from openai import AsyncClient
from core.models import db_helper
from services.crud import get_ai_use
from typing import List, Dict


class AI:
    def __init__(self, messages: List[Dict[str, str]]):
        self.messages: List[Dict[str, str]] = messages

    async def send(self) -> str | None:
        try:
            async with db_helper.scoped_session_dependency() as session:
                ai = await get_ai_use(session)

            client = AsyncClient(
                api_key=ai.api_key,
                base_url=ai.base_url,
            )

            try:

                result = await client.chat.completions.create(
                    model=ai.model,
                    messages=self.messages,
                )
                response = result.choices[0].message.content
                return response
            except Exception as e:
                return None

        except Exception as e:
            raise e
