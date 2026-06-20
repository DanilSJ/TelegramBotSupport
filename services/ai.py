from openai import AsyncClient
from openai import AuthenticationError

from core.config import settings
from core.models import db_helper
from services.crud import get_ai_use


class AI:
    def __init__(self, prompt: str):
        self.prompt: str = prompt

    async def send(self) -> str | None:
        try:
            async with db_helper.scoped_session_dependency() as session:
                ai = await get_ai_use(session)

            client = AsyncClient(
                api_key=settings.AI_TOKEN,
                base_url=settings.BASE_URL,
            )

            try:
                result = await client.chat.completions.create(
                    model=ai.model,
                    messages=[
                        {"role": "system", "content": ai.system_prompt},
                        {
                            "role": "user",
                            "content": self.prompt,
                        },
                    ],
                )
                response = result.choices[0].message.content

                return response
            except AuthenticationError:
                return None

        except Exception as e:
            raise e
