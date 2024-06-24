import json
import asyncio
import openai
from textwrap import dedent
from dotenv import load_dotenv

load_dotenv()

client = openai.AsyncOpenAI()


async def get_completion(system_message, prompt) -> str:
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]
    response = await client.chat.completions.create(
        messages=messages, model="gpt-4o", temperature=0
    )
    return response.choices[0].message.content


async def get_topic_list(raw_text: str) -> dict:
    system_message: str = dedent("""
    Your task is to separate the given study material into topics and subtopics
    by outputting a recursively-nested dictionary. Details are a description
    of the knowledge required, not the knowledge itself. Details are always
    required but subtopics are optional if not in the data. Details must only
    contain information that is not covered by the subtopics. If subtopics is 
    empty then you must omit the key.
    Your output must be directly JSON-parseable (output no outside text):
    [
        {
            name: str,
            "detail_list": list[str],
            "subtopic_list": [
                {
                    name: str,
                    "detail_list": list[str],
                    "subtopic_list" {...}
                },
                {...}
            ]
        },
        {...}
    ]
    """)
    output = await get_completion(system_message, raw_text)
    print(output)
    return json.loads(output)


def get_topic_list_info(topic_list: list[dict], queue: asyncio.Queue):
    for topic in topic_list:
        asyncio.create_task(get_topic_info(topic, queue))


async def get_topic_info(topic: dict, queue: asyncio.Queue):
    system_message = dedent("""
    Output comprehensive information of the topic in the given detail_list as markdown,
    covering enough information to ace any exam on it. You'll be given the topic for context. 
    Output only the information, no filler or introductory text.
    """)
    
    detail_list = topic.get("detail_list")
    name = topic.get('name')
    if detail_list:
        prompt = f"Topic: {name}\nDetail List: {detail_list}"
        topic['info'] = await get_completion(system_message, prompt)
        await queue.put(topic['info'])

    subtopic_list = topic.get("subtopic_list")
    if subtopic_list:
        get_topic_list_info(subtopic_list, queue)