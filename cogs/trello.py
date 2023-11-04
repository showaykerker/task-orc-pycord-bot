import os
import json
import random
from typing import List
from itertools import cycle

from discord import ApplicationContext
from discord import Option
from ezcord.internal.dc import discord as dc
from ezcord import Bot, Cog
from trello import TrelloClient

class Trello(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)

    @dc.slash_command(
        name="set_trello", description="Set trello key and token"
    )
    async def set_trello(
            self,
            ctx: ApplicationContext,
            key: Option(str),
            token: Option(str)) -> None:
        await self.bot._db.set_trello_key_token(ctx.guild_id, key, token)
        await self.get_boards(ctx)

    @dc.slash_command(
        name="get_boards", description="Get all boards"
    )
    async def get_boards(self, ctx: ApplicationContext) -> None:
        key, token = await self.bot._db.get_trello_key_token(ctx.guild_id)
        client = TrelloClient(
            api_key=key,
            api_secret=token,
        )
        all_boards = client.list_boards()
        embed = dc.Embed(
            title = "Trello上的看板:",
            color=dc.Colour.fuchsia()
        )
        for board in all_boards:
            desc = "*No description*"
            if len(board.description) > 1024:
                desc = "*敘述過長無法顯示*"
            elif board.description:
                desc = f"*{board.description}*"
            
            embed.add_field(name=board.name, value=desc, inline=False)
        await ctx.respond(embed=embed)


def setup(bot: Bot):
    # Uncomment the following line to install this cog.
    bot.add_cog(Trello(bot))
