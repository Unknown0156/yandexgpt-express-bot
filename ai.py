import logging
import aiohttp

import settings


url = settings.yandex_url
api_key = settings.yandex_api_key
headers = {
    "Content-Type": "application/json",
    "Authorization": "Api-Key " + api_key
}

async def generate_text(history):
    data = {
        "model": "general",
        "generation_options": {
            "partialResults": True,
            "max_tokens": 1500,
            "temperature": 0.6
        },
        "messages": [],
        "instruction_text": "",   
    }
    data["messages"]=history
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                async for line in response.content.iter_any():
                    yield line.decode('utf-8')
    except Exception as e:
        logging.error(e)