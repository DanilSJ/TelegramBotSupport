from openai import AsyncClient
from core.config import settings


class AI:
    def __init__(self, prompt: str):
        self.client = AsyncClient(
            api_key=settings.AI_TOKEN,
            base_url=settings.BASE_URL,
        )
        self.model: str = "deepseek-chat"
        self.system_prompt: str = """
        Стиль общения: Вежливый, лаконичный, деловой. Исключены эмоциональные окраски и "водянистые" фразы
        Если вопрос не соответствует тематике, бот обязан прервать обсуждение и выдать стандартизированный ответ:  
  > *«Я помогаю только с вопросами по [Тематика]. Чем я могу помочь по делу?»*
        Вот вопросы на которые ты можешь отвечать и вот к ним ответы
        
        """
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
