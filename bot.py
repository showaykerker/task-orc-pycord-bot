import os

import asyncio
import dotenv
import discord
import ezcord
from cogwatch import watch

dotenv.load_dotenv()

class TaskOrc(ezcord.Bot):
    def __init__(self):
        super().__init__(
            intents=discord.Intents.default(),
            language="ch")
        self.add_help_command()
        self.load_cogs("cogs")

    @watch(path="cogs", preload=True, debug=True)
    async def on_ready(self):
        print("Bot ready.")

async def main():
    client = TaskOrc()
    await client.start(str(os.getenv("TOKEN")))

if __name__ == "__main__":
    asyncio.run(main())