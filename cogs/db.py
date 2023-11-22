import json
import os
import random
import sys

from itertools import cycle

from discord import ApplicationContext
from discord import Option
from discord.commands import SlashCommandGroup
from discord.commands import guild_only
from discord.ext.commands import has_any_role
from ezcord import Bot
from ezcord import Cog
from ezcord.internal.dc import discord as dc
from pandas import DataFrame as df
from table2ascii import PresetStyle
from table2ascii import table2ascii as t2a

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constant_values import admin_roles


def df_to_ascii_table(df:df) -> str:
    fields = ["name", "discord_id", "trello_id"]
    body = [[df[f][i] for f in fields] for i in df.index]
    fields = ["Name", "DiscordID", "TrelloID"]

    # Trim name length
    max_length = 16
    for i, mem in enumerate(body):
        if len(mem[0]) > max_length:
            body[i][0] = mem[0][:max_length-2] + ".."

    table = t2a(
        header = fields,
        body = body,
        style = PresetStyle.simple,
        column_widths = [max_length, 22, 26],
        cell_padding=0,
        use_wcwidth=True,
    )
    return f"```\n{table}\n```"

class Database(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)

    db_cmd = SlashCommandGroup("db", "db operations")
    getters = db_cmd.create_subgroup("get", "getters")

    @getters.command(
        name="members", description="Get member data from database.",
    )
    @guild_only()
    @has_any_role(*admin_roles)
    async def members(self, ctx: ApplicationContext) -> None:
        await self._get_members(ctx, f"{ctx.guild} 的成員們")

    async def _get_members(self, ctx: ApplicationContext, title: str) -> None:
        member_list = await self.bot.db.get_member_data(ctx.guild_id)
        title = title if title else f"{ctx.guild} 的成員們"
        await ctx.respond(f"**{title}**\n{df_to_ascii_table(member_list)}")




def setup(bot: Bot):
    # Uncomment the following line to install this cog.
    bot.add_cog(Database(bot))
