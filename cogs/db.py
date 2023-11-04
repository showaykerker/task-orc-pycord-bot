import os
import json
import random
from itertools import cycle

from discord import ApplicationContext
from discord import Option
from ezcord.internal.dc import discord as dc
from ezcord import Bot, Cog
from pandas import DataFrame as df
from table2ascii import table2ascii as t2a
from table2ascii import PresetStyle


def df_to_ascii_table(df:df) -> str:
    fields = ["name", "discord_id", "trello_id"]
    body = [[df[f][i] for f in fields] for i in df.index]
    fields = ["Name", "DiscordID", "TrelloID"]

    # Trim name length
    max_length = 8
    for i, mem in enumerate(body):
        if len(mem[0]) > max_length:
            body[i][0] = mem[0][:max_length-2] + ".."

    table = t2a(
        header = fields,
        body = body,
        style = PresetStyle.simple,
        column_widths = [8, 18, 24],
        cell_padding=0,
        use_wcwidth=True,
    )
    return f"```\n{table}\n```"

class Database(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)

    @dc.slash_command(
        name="get", description="Get data from the database"
    )
    async def get(self, ctx: ApplicationContext, field: Option(str, choices=["members",])) -> None:
        if field == "members":
            await self.get_members(ctx)

    @dc.slash_command(
        name="get_members", description="Get member data from database.",
    )
    async def get_members(self, ctx, title_overwrite="") -> None:
        member_list = await self.bot._db.get_member_data(ctx.guild_id)
        title = title_overwrite if title_overwrite else f"{ctx.guild} 的成員們"
        embed = dc.Embed(
            title = title,
            color=dc.Colour.fuchsia()
        )
        embed.add_field(name="", value=df_to_ascii_table(member_list), inline=True)

        await ctx.respond(embed=embed)

    @dc.slash_command(
        name="set_members", description="Set member data to database.",
    )
    async def set_members(self, ctx) -> None:
        members = ctx.guild.members
        member_list = []
        for member in members:
            # skip robot members
            if member.bot:
                continue
            member_list.append({
                "name": member.name,
                "discord_id": member.id,
                "trello_id": ""
            })
        await self.bot._db.set_member_data(ctx.guild_id, member_list)
        
        await self.get_members(ctx, "以下的成員已經成功加到資料庫中。")

    @dc.slash_command(
        name="set_trello", description="Set trello key and token"
    )
    async def set_trello(self, ctx: ApplicationContext, key: Option(str), token: Option(str)) -> None:
        await self.bot._db.set_trello_key_token(ctx.guild_id, key, token)


    


def setup(bot: Bot):
    # Uncomment the following line to install this cog.
    bot.add_cog(Database(bot))
