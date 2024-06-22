from discord import Intents, Bot, Message, Member
from pipeline import pipeline
from dotenv import load_dotenv
import os
load_dotenv()

# Initialization and Global Variables
bot = Bot(intents=Intents.all())
me: Member = None
gf: Member = None

@bot.event
async def on_message(message: Message):
    if message.guild is not None:
        return

    prompt = message.content
    response = pipeline(prompt)
    await message.reply(response)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Main Execution
if __name__ == "__main__":
    bot.run(os.environ['DISCORD_TOKEN'])
