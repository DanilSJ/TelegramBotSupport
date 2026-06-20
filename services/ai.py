from openai import AsyncClient
from core.models import db_helper
from services.crud import get_ai_use


class AI:
    def __init__(self, prompt: str):
        self.prompt: str = prompt

    async def send(self):
        try:
            async with db_helper.scoped_session_dependency() as session:
                ai = await get_ai_use(session)

            client = AsyncClient(
                api_key=ai.api_key,
                base_url=ai.base_url,
            )

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
        except Exception as e:
            raise e
