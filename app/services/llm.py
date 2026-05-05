from openai import OpenAI
from app.core import settings

client = OpenAI(api_key=settings.openai_api_key)


def generate_response(message: str) -> str | None:
    response = client.chat.completions.create(
        model=settings.model_name,
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": message},
        ],
        max_tokens=settings.max_tokens,
    )
    return response.choices[0].message.content
