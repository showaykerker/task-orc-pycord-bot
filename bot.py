import os

import asyncio
import dotenv
import discord
import ezcord
from cogwatch import watch

from database_handler import TaskOrcDB
from trello_handler import TrelloHandler

dotenv.load_dotenv()

class TaskOrc(ezcord.Bot):
    def __init__(self):
        super().__init__(
            intents=discord.Intents.default(),
            language="ch")
        self.add_help_command()
        self.load_cogs("cogs")
        self.db = TaskOrcDB()
        self.trello = TrelloHandler()

    @watch(path="cogs", preload=True, debug=True)
    async def on_ready(self):
        await self.db.setup()
        print("Bot ready.")


async def main():
    client = TaskOrc()
    await client.start(str(os.getenv("TOKEN")))

if __name__ == "__main__":
    asyncio.run(main())