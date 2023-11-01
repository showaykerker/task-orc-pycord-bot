import os
import json
import random
from itertools import cycle

from discord import ApplicationContext
from ezcord.internal.dc import discord as dc
from ezcord import Bot, Cog
from pandas import DataFrame as df
from table2ascii import table2ascii as t2a
from table2ascii import PresetStyle

def df_to_ascii_table(df:df) -> str:
    fields = ["name", "discord_id", "trello_id"]
    body = [[df[f][i] for f in fields] for i in df.index]

    # Trim name length
    max_length = 10
    for i, mem in enumerate(body):
        if len(mem[0]) > max_length:
            body[i][0] = mem[0][:max_length-2] + ".."

    table = t2a(
        header = fields,
        body = body,
        style = PresetStyle.thick_compact,
        cell_padding=0
    )
    return f"```\n{table}\n```"

class Database(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)

    @dc.slash_command(
        name="get_members", description="Get member data from database."
    )
    async def get_members(self, ctx) -> None:
        member_list = await self.bot._db.get_member_data(ctx.guild_id)
        embed = dc.Embed(
            title = f"{ctx.guild} 的成員們",
            description = df_to_ascii_table(member_list),
            color=dc.Colour.fuchsia()
        )

        await ctx.respond(embed=embed)


def setup(bot: Bot):
    # Uncomment the following line to install this cog.
    bot.add_cog(Database(bot))
