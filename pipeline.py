import json
import openai
from copy import deepcopy
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
        messages, model="gpt-4o", temperature=0
    )
    return response.choices[0].message.content


async def get_topics(raw_text: str) -> dict[str, dict]:
    system_message: str = dedent("""
    Your task is to separate the given study material into topics and sub-topics
    by outputting a recursively-nested dictionary. Details are a description
    of the knowledge required, not the knowledge itself. Details are always
    required but sub-topics are optional if not in the data. Details must only
    contain information that is not covered by the sub-topics.
    Your output must be directly JSON-parseable:
    {
        "Topic Name": {
            "detail_list": list[str],
            "sub_topics": [
                {
                    "Topic Name": { 
                        "detail_list": list[str],
                        "sub_topics" [...]
                    }
                }
            ]
        },
        "Topic Name": {...}
    }
    """)
    output = await get_completion(system_message, raw_text)
    return json.loads(output)

async def inject_topics_knowledge(topics: dict[str, dict]) -> dict[str, dict]:
    new_topics = deepcopy(topics)
    system_message = dedent("""
    Convert the given detail_list into comprehensive markdown covering enough information to 
    ace any exam on it. You'll be given the topic for context. Output only the information,
    no filler or introductory text.
    """)
    for topic_name, topic_data in new_topics.items():
        detail_list = topic_data.get('detail_list')
        if not detail_list:
            return None
        
        prompt = f"Topic: {topic_name}\nDetail List: {detail_list}"
        topic_data['info'] = await get_completion(system_message, prompt)
        sub_topics = topic_data.get('sub_topics')
        if sub_topics:
            sub_topics = await inject_topics_knowledge(sub_topics)
                
async def stringify_topics(topics: dict[str, dict], nesting_level=0, string_list=None) -> str:
    string_list = string_list or []
    for topic_name, topic_data in topics.items():
        title = '#' * (nesting_level + 1) + ' ' + topic_name
        string_list.append('\t' * nesting_level + title)
        string_list.append('\t' * nesting_level + topic_data['info'])
    
    sub_topics = topic_data.get('sub_topics')
    if sub_topics:
        await stringify_topics(sub_topics, nesting_level + 1, string_list)
    
    return '\n'.join(string_list)

async def pipeline(raw_text: str) -> str:
    topics = await get_topics(raw_text)
    topics = await inject_topics_knowledge(topics)
    markdown_string = await stringify_topics(topics)
    return markdown_string
