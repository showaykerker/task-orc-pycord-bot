import os
import json
import random
from itertools import cycle

from discord import ApplicationContext
from discord import Option
from ezcord.internal.dc import discord as dc
from ezcord import Bot, Cog


class Trello(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)

    @dc.slash_command(
        name="set_trello", description="Set trello key and token"
    )
    async def set_trello(self, ctx: ApplicationContext, key: Option(str), token: Option(str)) -> None:
        await self.bot._db.set_trello_key_token(ctx.guild_id, key, token)


def setup(bot: Bot):
    # Uncomment the following line to install this cog.
    bot.add_cog(Trello(bot))
