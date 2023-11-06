import os
import sys
import json
import random
from typing import List, Optional
from itertools import cycle

from discord import ApplicationContext
from discord import Option
from discord.commands import SlashCommandGroup
from ezcord.internal.dc import discord as dc
from ezcord import Bot, Cog, emb
from trello import TrelloClient
from table2ascii import table2ascii as t2a
from table2ascii import PresetStyle

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from views import SetTrelloUserIdView

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

    trello_cmd = SlashCommandGroup("trello", "trello operations")
    tgetters = trello_cmd.create_subgroup("get", "getters")
    tsetters = trello_cmd.create_subgroup("set", "setters")

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

    trello_get = SlashCommandGroup("trello_get", "Getters")

    @dc.slash_command(
        name="configure_trello", description="Set trello key and token"
    )
    async def configure_trello(
            self,
            ctx: ApplicationContext,
            key: Option(str),
            token: Option(str)) -> None:
        is_updated = await self.bot.db.set_trello_key_token(ctx.guild_id, key, token)
        if is_updated:
            await emb.success(ctx, "Trello key and token updated.")
            self.bot.trello.remove_client(ctx.guild_id)
        trello = await self.get_trello_instance(ctx)

        # Update guild member list
        await self.bot.db.configure_guild_members(ctx)
        member_list = await self.bot.db.get_member_data(ctx.guild_id)
        trello_id_to_name_dict = await self.bot.trello.get_members(trello)

        members_in_guild_to_be_assigned = dict(
            [(m, i) for m, i in zip(member_list['name'], member_list['discord_id'])])
        trello_candidates = trello_id_to_name_dict
        trello_candidates["None"] = "None"
        is_set_callback = lambda discord_id, trello_id: self.bot.db.update_trello_id(ctx.guild_id, discord_id, trello_id)
        view = SetTrelloUserIdView(members_in_guild_to_be_assigned, trello_candidates, is_set_callback)
        await ctx.followup.send("用下拉選單設定成員名稱對照", view=view)


    @tgetters.command(
        name="boards", description="Get all boards"
    )
    async def boards(self, ctx: ApplicationContext) -> None:
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

    @tgetters.command(
        name="members", description="Get all Trello Users Info"
    )
    async def get_trello_members(self, ctx: ApplicationContext) -> None:
        trello = await self.get_trello_instance(ctx)
        if trello is None: return

        embed = dc.Embed(
            title = "Trello上的成員:",
            color=dc.Colour.fuchsia()
        )
        member_id_to_name_dict = await self.bot.trello.get_members(trello)

        embed.add_field(name="", value=dict_to_ascii_table(member_id_to_name_dict), inline=True)
        await ctx.respond(embed=embed)

    @tgetters.command(
        name="undone", description="Get all undone cards"
    )
    async def get_trello_undone(self, ctx: ApplicationContext) -> None:
        trello = await self.get_trello_instance(ctx)
        if trello is None: return
        await ctx.defer()
        cards = self.bot.trello.get_undone(trello)
        embed = dc.Embed(
            title = "待完成的卡片們",
            color = dc.Colour.fuchsia()
        )
        board_id_to_name = self.bot.trello.get_board_names(ctx.guild_id)
        if cards:
            for i, c in enumerate(cards._c):
                value = ""
                member_str = ""
                if c.due:
                    value += f"{c.due}\n"
                for j, m in enumerate(c.members):
                    value += f"{m}"
                    if j != len(c.members) -1:
                        value += ", "
                if c.members:
                    value += "\n"
                value += f"{board_id_to_name.get(c.board)} - {c.list.name}\n"
                embed.add_field(
                    name=f"{c.title}", value=value, inline=(i%2)==0)
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
