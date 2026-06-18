from openai import AsyncClient
from core.settings import settings


class AI:
    def __init__(self, prompt: str):
        self.client = AsyncClient(
            api_key=settings.AI_TOKEN,
            base_url=settings.BASE_URL,
        )
        self.model: str = ""
        self.system_prompt: str = ""
        self.prompt: str = prompt

    async def send(self):
        try:
            result = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
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
