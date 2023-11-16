import os
import re

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
            intents=discord.Intents.all(),
            language="ch")
        self.add_help_command()
        self.load_cogs("cogs")
        self.db = TaskOrcDB()
        self.trello = TrelloHandler()
        self.add_listener(self.on_events_forward, "on_message")

    @watch(path="cogs", preload=True, debug=True)
    async def on_ready(self):
        await self.db.setup()
        print("Bot ready.")

    async def on_events_forward(self, message):
        # Forward message from other robot
        if message.author.id == self.user.id or\
                message.channel.name != "events" or\
                not message.author.bot:
            return

        pattern = re.compile(r".* \[(.*)\].*")
        match = pattern.match(message.content)
        if match is None: return

        match_targets = match.group(1).split(" ")
        channels = await message.guild.fetch_channels()
        for channel in channels:
            if channel.name in match_targets:
                await channel.send(message.content)
                break

client = TaskOrc()
client.run(str(os.getenv("TOKEN")))
