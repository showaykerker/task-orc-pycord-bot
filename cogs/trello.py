import datetime
import json
import math
import os
import random
import re
import sys

from itertools import cycle
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import discord
import numpy as np

from discord import ApplicationContext
from discord import InteractionResponse
from discord import Option
from discord.commands import SlashCommandGroup
from discord.commands import guild_only
from discord.ext import commands
from discord.ext.commands import has_any_role
from discord.ext.pages import Page
from discord.ext.pages import Paginator
from ezcord import Bot
from ezcord import Cog
from ezcord import emb
from ezcord.internal.dc import discord as dc
from table2ascii import Merge
from table2ascii import PresetStyle
from table2ascii import table2ascii as t2a
from trello import TrelloClient
from wcwidth import wcswidth

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constant_values import admin_roles
from constant_values import board_emojis
from constant_values import charater_emojis
from constant_values import due_emojis
from trello_handler import no_trello_error_msg
from trello_handler import get_trello_instance
from trello_handler import DateCard
from trello_handler import FilteredCards
from trello_handler import TrelloDummyAssign
from utils import task_parser


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
        bot.add_listener(self.on_message)

    trello_cmd = SlashCommandGroup("trello", "trello operations")
    tgetters = trello_cmd.create_subgroup("get", "getters")

    @tgetters.command(
        name="boards", description="Get all boards"
    )
    @guild_only()
    async def boards(self, ctx: ApplicationContext) -> None:
        trello = await get_trello_instance(self, ctx)
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
    @guild_only()
    async def get_trello_members(self, ctx: ApplicationContext) -> None:
        trello = await get_trello_instance(self, ctx)
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
    @guild_only()
    async def get_trello_undone(
            self,
            ctx: ApplicationContext,
            user: str=Option(str, choices=['me', 'all'], default='me', required=False)) -> None:
        trello = await get_trello_instance(self, ctx)
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

        embed = dc.Embed(
            title=title,
            color=dc.Colour.lighter_grey()
        )
        card_length = 18
        list_of_dict_cards = filtered_cards.to_list_of_dict(
            trello_id_to_discord_name = trello_id_to_discord_name,
            member_max_length = card_length-2)
        for card_dict in list_of_dict_cards:
            card_link = f" [↗↗](<{card_dict['url']}>) " if card_dict["url"] else "—"*5
            value = f'{random.choice(charater_emojis)} {card_dict["members"]}\n' if card_dict["members"] else ""
            if show_board:
                value += f'{random.choice(board_emojis)} {card_dict["board"]}\n'
            value += f'{random.choice(due_emojis)} {card_dict["due"]} \n' if card_dict["due"] else ""
            value += "\n" if value == "" else ""
            value += f'{"—"*4}{card_link}{"—"*4}\n'
            embed.add_field(
                name=f':jigsaw:{card_dict["title"]}',
                value=value,
                inline=True)
        return embed

    @tgetters.command(name="all_undone", description="Get all undone cards")
    @guild_only()
    async def get_all_trello_undone(self, ctx: ApplicationContext) -> None:
        await self.get_trello_undone(ctx, user="all")


    async def on_message(self, message: discord.Message) -> None:

        if message.author.bot or not message.content.startswith("<@1163852103958155375>"):
            return

        msgs = message.clean_content.split("\n")[1:]
        tasks = task_parser.parse_tasks(msgs)

        trello = await get_trello_instance(self, message.guild.id)
        if trello is None: return

        dn2ti = await self.bot.db.get_discord_name_to_trello_id_dict(message.guild.id)
        trello_settings = await self.bot.db.get_trello_settings(message.guild.id)
        board_list_data = await self.bot.trello.get_board_list_data(message.guild.id)
        assignments = tasks.get("task_assignment")
        filtered_cards = FilteredCards()
        card_add_info = {"board_ids": [], "list_ids": [], "names": [], "dues": [], "assigns": []}

        for key, due_tasks in assignments.items():
            key = "" if key == np.inf else key
            if "everyone" in key:
                member_id = [TrelloDummyAssign(tid) for tid in dn2ti.values()]
            else:
                member_id = [TrelloDummyAssign(dn2ti.get(key)), ] if dn2ti.get(key) else []
            for due_str, tasks in due_tasks.items():
                if isinstance(due_str, float):
                    due = ""
                else:
                    due = datetime.datetime.strptime(due_str, "%Y/%m/%d").date()

                # Handle assigned tasks
                for task in tasks:

                    # Keyword overwrite with ||Overwrite Patterns||
                    keyword_overwrite = None
                    pattern = r".*(\|\|(.*)\|\|) *$"
                    match = re.match(pattern, task)
                    if match:
                        task = task.replace(match.group(1), "")
                        keyword_overwrite = "default" if match.group(2) == "" else match.group(2)

                    # Assign task to board
                    assigned_board_id = None
                    if keyword_overwrite:
                        for board_id, keywords in trello_settings.board_keywords.items():
                            if str(keyword_overwrite).lower() in keywords.split(","):
                                assigned_board_id = board_id
                    else:
                        for board_id, keywords in trello_settings.board_keywords.items():
                            if board_id not in trello_settings.board_id_list_id_to_create_card.keys():
                                emb.error(
                                    message,
                                    f"看板{board_name}沒有設定新增卡片的位置，"\
                                    "請使用`/set_trello_board_list_to_create`設定。")
                            if any([kw in task.lower() for kw in keywords.split(",")]):
                                    break

                    assigned_board_id = trello_settings.default_board if assigned_board_id is None else assigned_board_id
                    assigned_board_name = board_list_data.board_id_to_name[assigned_board_id]

                    # Find list id to create card
                    list_id = trello_settings.board_id_list_id_to_create_card[assigned_board_id]
                    list_name = board_list_data.list_id_to_name[list_id]

                    # Create cards to be added
                    filtered_cards.plain_append(DateCard(
                        board = assigned_board_name,
                        t_list = list_name,
                        title = task,
                        members = [key, ],
                        due = due))
                    card_add_info["board_ids"].append(assigned_board_id)
                    card_add_info["list_ids"].append(list_id)
                    card_add_info["names"].append(task)
                    card_add_info["dues"].append(due)
                    card_add_info["assigns"].append(member_id)
        card_add_info["serials"] = [i for i in range(len(card_add_info["names"]))]

        if filtered_cards:
            embed = self.get_embed_from_filtered_cards(
                title="要新增的卡片:",
                filtered_cards=filtered_cards,
                show_board=True
            )
            sent_msg = await message.reply(embed=embed)
            created_cards = await self.bot.trello.add_cards(trello, **card_add_info)

            # Replace the last line and name if added.
            for i, field in enumerate(embed.fields):
                card = created_cards.get(i)
                if card:
                    last_line = f'\n{"—"*4} [↗↗](<{card.short_url}>) {"—"*4}\n'
                    field.name = field.name.replace(":jigsaw:", ":white_check_mark:")
                else:
                    last_line = f'\n{"—"*3} Create Failed {"—"*3}\n'
                    field.name = field.name.replace(":jigsaw:", ":x:")
                field.value = "\n".join(field.value.split("\n")[:-2]) + last_line

            await sent_msg.edit(embed=embed)

        else:
            await message.reply("No cards to be created.")


def setup(bot: Bot):
    # Uncomment the following line to install this cog.
    bot.add_cog(Trello(bot))
