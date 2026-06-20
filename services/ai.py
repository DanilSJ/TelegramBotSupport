from openai import AsyncClient
from openai import AuthenticationError
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
                api_key="eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCIsImtpZCI6IjFrYnhacFJNQGJSI0tSbE1xS1lqIn0.eyJ1c2VyIjoiZWozNzkzNjEiLCJ0eXBlIjoiYXBpX2tleSIsImFwaV9rZXlfaWQiOiIwZmQyZGRkMS00M2ZkLTRhZGQtYmY0OC1hNjFkZDE3MTUzZjEiLCJpYXQiOjE3ODE5NDA2MTB9.R8qVV0s1aiWTLhiLTjY43aqV3iEQLE-fcdeEg6FA1IohsiRWzaoiNC6H-2jx7vqJ_xLdVt7e-lBpmmRhPi4S6kQPrMcZQRdToms6AJ4U1ZuqJzBw7-GC6_0tktz9mmdm5YN296YZLey-5LTz_scpFeZcrmj0FChIIBA7EqqZu7MgkC8_wyoendtwcwUFeJKq1T7wX3wgsWqVc_jPQ-JXl5kL9HbdOFn0M9fV-cLv3117rhJ7QJ3sgkev8fk7rsQMbwa869q8dbEP28omVj6V62gImegy8-XJQsqsHouCpXC2XuwJco30LQRLRDoKySx4QfkZTB5VWB8fXKT4lsvnrzE7biQk2kMwnKsomuEcqym7cMPRVYHpu6kibxI0x4EHN6ctNXlyw8q6q720zPzISGJ1Zj7ccrAwNC2yIJ0l91Wy29zY5NJ7gsm5eSfcqj0l5Enm2qz8keXbfabgeyw8APBV7hQtLH8MUQ-DqB84yjwBlHWtXLgevDWnFz5hfReR",
                base_url="https://agent.timeweb.cloud/api/v1/cloud-ai/agents/7a89f8df-fe76-4d81-8484-ef5bf4d590a3/v1",
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
