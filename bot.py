import asyncio
from discord import Intents, Bot, Message, Member
import pipeline
from dotenv import load_dotenv
import os
load_dotenv()

# Initialization and Global Variables
bot = Bot(intents=Intents.all())
me: Member = None
gf: Member = None

async def consumer(message: Message, queue: asyncio.Queue):
    while True:
        msg = await queue.get()
        chunks = msg.split('\n\n')
        for chunk in chunks:
            await message.channel.send(chunk)
        queue.task_done()
        
@bot.event
async def on_message(message: Message):
    if message.guild is not None or message.author == bot.user:
        return

    prompt = message.content
    queue = asyncio.Queue()
    topic_list = await pipeline.get_topic_list(prompt)
    if not topic_list:
        await message.channel.send("Invalid input.")
    
    producer_task = asyncio.create_task(pipeline.get_topic_list_info(topic_list, queue))
    consumer_task = asyncio.create_task(consumer(message, queue))
    
    await producer_task
    await queue.join()
    consumer_task.cancel()
    await consumer_task


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Main Execution
if __name__ == "__main__":
    bot.run(os.environ['DISCORD_TOKEN'])
