import os
import json
import random
from typing import List, Optional
from itertools import cycle

from discord import ApplicationContext
from discord import Option
from ezcord.internal.dc import discord as dc
from ezcord import Bot, Cog, emb
from trello import TrelloClient
from table2ascii import table2ascii as t2a
from table2ascii import PresetStyle

no_trello_error_msg = lambda ctx: emb.error(
    ctx, "No Trello configuration found. Use /configure_trello First.") 

def dict_to_ascii_table(id_to_name: dict) -> str:
    fields = ["TrelloID", "Name"]
    body = [[_id, name] for _id, name in id_to_name.items()]

    # Trim name length
    max_length = 12
    for i, mem in enumerate(body):
        if len(mem[1]) > max_length:
            body[i][1] = mem[1][:max_length-2] + ".."

    table = t2a(
        header = fields,
        body = body,
        style = PresetStyle.simple,
        cell_padding=1,
        use_wcwidth=True,
    )
    return f"```\n{table}\n```"

class Trello(Cog):

    def __init__(self, bot: Bot):
        super().__init__(bot)

    async def get_trello_instance(
            self,
            ctx: ApplicationContext) -> TrelloClient:
        if not self.bot.trello.contains_guild(ctx.guild_id):
            key, token = await self.bot.db.get_trello_key_token(ctx.guild_id)
            if key is None or token is None:
                await no_trello_error_msg(ctx)
                return
            self.bot.trello.add_client(ctx.guild_id, key, token)
        trello = self.bot.trello[ctx.guild_id]
        if trello:
            return trello
        await no_trello_error_msg(ctx)
        return 

    @dc.slash_command(
        name="congifure_trello", description="Set trello key and token"
    )
    async def congifure_trello(
            self,
            ctx: ApplicationContext,
            key: Option(str),
            token: Option(str)) -> None:
        await self.bot.db.set_trello_key_token(ctx.guild_id, key, token)
        trello = await self.get_trello_instance(ctx, key, token)
        await self.get_boards(ctx)

    @dc.slash_command(
        name="get_boards", description="Get all boards"
    )
    async def get_boards(self, ctx: ApplicationContext) -> None:
        trello = await self.get_trello_instance(ctx)
        if trello is None: return

        all_boards = trello.list_boards()
        embed = dc.Embed(
            title = "Trello上的看板:",
            color=dc.Colour.fuchsia()
        )
        for board in all_boards:
            desc = "*No description*"
            if len(board.description) > 102:
                desc = f"{board.description[:100]}.."
            elif board.description:
                desc = f"*{board.description}*"
            
            embed.add_field(name=board.name, value=desc, inline=False)
        await ctx.respond(embed=embed)

    @dc.slash_command(
        name="get_trello_users", description="Get all Trello Users Info"
    )
    async def get_trello_users(self, ctx: ApplicationContext) -> None:
        trello = await self.get_trello_instance(ctx)
        if trello is None: return

        all_boards = trello.list_boards()
        embed = dc.Embed(
            title = "Trello上的成員:",
            color=dc.Colour.fuchsia()
        )
        member_id_to_name_dict = {}
        for board in all_boards:
            for m in board.all_members():
                member_id_to_name_dict[m.id] = m.full_name

        embed.add_field(name="", value=dict_to_ascii_table(member_id_to_name_dict), inline=True)
        await ctx.respond(embed=embed)

    @dc.slash_command(
        name="get_trello_undone", description="Get all undone cards"
    )
    async def get_trello_undone(self, ctx: ApplicationContext) -> None:
        trello = await self.get_trello_instance(ctx)
        if trello is None: return

        await ctx.defer()

        all_boards = trello.list_boards()
        embed = dc.Embed(
            title = "Trello上的看板:",
            color=dc.Colour.fuchsia()
        )
        for card in trello.search(
                "-label:header is:open sort:due -list:done -list:ideas -list:resources",
                models=["cards",]):
            print(card.name)
            embed.add_field(name=card.name, value=card.member_id)
        print(embed)
        await ctx.followup.send(embed=embed)

    # Not used.
    # @dc.slash_command(
    #     name="get_trello_lists", description="Get all Trello Lists"
    # )
    # async def get_trello_lists(self, ctx: ApplicationContext) -> None:
    #     trello = await self.get_trello_instance(ctx)
    #     if trello is None: return

    #     all_boards = trello.list_boards()
    #     embed = dc.Embed(
    #         title = "Trello上的看板:",
    #         color=dc.Colour.fuchsia()
    #     )
    #     for board in all_boards:
    #         embed.add_field(name=board.name, value="", inline=False)
    #         for lst in board.list_lists():
    #             embed.add_field(name=lst.name, value=lst.id, inline=True)
    #     await ctx.respond(embed=embed)

    # To be modified
    # @dc.slash_command(
    #     name="get_trello_cards", description="Get all Trello Cards"
    # )
    # async def get_trello_cards(self, ctx: ApplicationContext) -> None:
    #     trello = await self.get_trello_instance(ctx)
    #     if trello is None: return

    #     await ctx.defer()

    #     all_boards = trello.list_boards()
    #     embed = dc.Embed(
    #         title = "Trello上的看板:",
    #         color=dc.Colour.fuchsia()
    #     )
    #     for board in all_boards:
    #         print(f"board {board}")
    #         embed.add_field(name=board.name, value="", inline=False)
    #         for card in board.all_cards():
    #             print(f"\tcard {card}")
    #             embed.add_field(name=card.name, value=card.description, inline=True)
    #     await ctx.followup.send(embed=embed)


def setup(bot: Bot):
    # Uncomment the following line to install this cog.
    bot.add_cog(Trello(bot))
