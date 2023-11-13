import os
import sys
import json
import math
import random
from typing import List, Optional
from itertools import cycle

from wcwidth import wcswidth
import discord
from discord import ApplicationContext
from discord import Option
from discord import InteractionResponse
from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord.ext.pages import Paginator, Page
from ezcord.internal.dc import discord as dc
from ezcord import Bot, Cog, emb
from trello import TrelloClient
from table2ascii import table2ascii as t2a
from table2ascii import PresetStyle
from table2ascii import Merge

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from views import SetTrelloUserIdView, SetTrelloTargetListView, SetTrelloBoardListToCreateCard
from constant_values import charater_emojis, due_emojis
from modals import BoardKeywordModal

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
        cell_padding=1
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
            await self.bot.trello.add_client(ctx.guild_id, key, token)
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
            key: Optional[str]=None,
            token: Optional[str]=None) -> None:
        await ctx.defer()
        if key and token:
            is_updated = await self.bot.db.set_trello_key_token(ctx.guild_id, key, token)
            if is_updated:
                await emb.success(ctx, "Trello key and token updated.")
                self.bot.trello.remove_client(ctx.guild_id)

        trello = await self.get_trello_instance(ctx)

        # Update guild member list
        await self.bot.db.configure_guild_members(ctx)
        member_list = await self.bot.db.get_member_data(ctx.guild_id)
        trello_id_to_name_dict = await self.bot.trello.get_members(trello)
        discord_name_to_trello_id_dict = await self.bot.db.get_discord_name_to_trello_id_dict(ctx.guild_id, member_list)
        discord_name_to_trello_name_dict = dict(
            [(m, trello_id_to_name_dict.get(i) or "") for m, i in zip(member_list['name'], member_list['trello_id'])])

        members_in_guild_to_be_assigned = dict(
            [(m, i) for m, i in zip(member_list['name'], member_list['discord_id'])])

        trello_id_to_name_dict["None"] = "None"
        is_set_callback = lambda discord_id, trello_id: self.bot.db.update_trello_id(ctx.guild_id, discord_id, trello_id)
        view = SetTrelloUserIdView(
            ctx,
            members_in_guild_to_be_assigned,
            trello_id_to_name_dict,
            is_set_callback,
            discord_name_to_trello_name_dict)
        await ctx.followup.send("用下拉選單設定成員名稱對照", view=view, embed=view.embed)

    @dc.slash_command(
        name="set_trello_list_to_trace"
    )
    async def set_trello_list_to_trace(self, ctx: ApplicationContext):
        await ctx.defer()
        trello = await self.get_trello_instance(ctx)
        if trello is None: return

        board_list_data = await self.bot.trello.get_board_list_data(ctx.guild_id)
        trello_settings = await self.bot.db.get_trello_settings(ctx.guild_id)

        view = SetTrelloTargetListView(ctx, board_list_data, trello_settings, self.bot.db)
        await ctx.followup.send("用下拉選單設定追蹤的看板", view=view, embed=view.embed)

    @dc.slash_command(name="set_trello_board_list_to_create")
    async def set_trello_board_list_to_create_card(self, ctx: ApplicationContext):
        await ctx.defer()
        trello = await self.get_trello_instance(ctx)
        if trello is None: return

        board_list_data = await self.bot.trello.get_board_list_data(ctx.guild_id)
        trello_settings = await self.bot.db.get_trello_settings(ctx.guild_id)

        view = SetTrelloBoardListToCreateCard(ctx, board_list_data, trello_settings, self.bot.db)
        await ctx.followup.send("用下拉選單設定新增卡片的位置", view=view, embed=view.embed)


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
    async def get_trello_undone(
            self,
            ctx: ApplicationContext,
            user: str=Option(str, choices=['me', 'all'], default='me', required=False)) -> None:
        trello = await self.get_trello_instance(ctx)
        if trello is None: return
        await ctx.defer()
        board_id_to_name = await self.bot.trello.get_board_names(ctx.guild_id)
        trello_id_to_discord_name = await self.bot.db.get_trello_id_to_discord_name_dict(ctx.guild_id)
        discord_id = ctx.user.id if user == "me" else None
        trello_id = await self.bot.db.get_trello_id_from_discord_id(ctx.guild_id, discord_id)
        trello_settings = await self.bot.db.get_trello_settings(ctx.guild_id)
        list_name_not_to_trace = trello_settings.list_name_not_to_trace
        filtered_cards = await self.bot.trello.get_undone(trello, trello_id, list_name_not_to_trace)
        if filtered_cards:
            embed = self.get_embed_from_filtered_cards(
                title="Trello上的未完成卡片:",
                filtered_cards=filtered_cards,
                trello_id_to_discord_name=trello_id_to_discord_name)
            try:
                if user == "me" and trello_id:
                    embed.add_field(
                        name="",
                        value=f"[»»»»»»»»»»»»»»](https://trello.com/u/{trello_id}/cards)",
                        inline=False)
            except discord.errors.ExtensionFailed:
                pass
            await ctx.followup.send(embed=embed)
        else:
            await ctx.followup.send("No undone cards found.")

    def get_embed_from_filtered_cards(
            self,
            title: str,
            filtered_cards: FilteredCards,
            trello_id_to_discord_name: Optional[Dict[str, str]] = {},
            show_board=False) -> dc.Embed:
        print(show_board)
        embed = dc.Embed(
            title=title,
            color=dc.Colour.lighter_grey()
        )
        card_length = 18
        list_of_dict_cards = filtered_cards.to_list_of_dict(
            trello_id_to_discord_name = trello_id_to_discord_name,
            member_max_length = card_length-2)
        for card_dict in list_of_dict_cards:
            card_link = f" [↗↗]({card_dict['url']}) " if card_dict["url"] else "—"*5
            value = f'{random.choice(charater_emojis)} {card_dict["members"]}\n' if card_dict["members"] else ""
            if show_board:
                value += f'{random.choice(board_emojis)} {card_dict["board"]}\n'
            value += f'{random.choice(due_emojis)} {card_dict["due"]} \n' if card_dict["due"] else ""
            value += "\n" if value == "" else ""
            value += f'{"—"*5}{card_link}{"—"*5}\n'
            embed.add_field(
                name=f':jigsaw:{card_dict["title"]}',
                value=value,
                inline=True)
        return embed


    @tgetters.command(name="all_undone", description="Get all undone cards")
    async def get_all_trello_undone(self, ctx: ApplicationContext) -> None:
        await self.get_trello_undone(ctx, user="all")

    @dc.slash_command(name="set_board_keywords")
    async def set_board_keywords(self, ctx: ApplicationContext) -> None:
        trello = await self.get_trello_instance(ctx)
        if trello is None: return

        board_list_data = await self.bot.trello.get_board_list_data(ctx.guild_id)
        trello_settings = await self.bot.db.get_trello_settings(ctx.guild_id)

        modal = BoardKeywordModal(ctx, board_list_data, trello_settings, self.bot.db)
        await ctx.send_modal(modal)

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
