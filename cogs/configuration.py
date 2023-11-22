import os
import sys
import asyncio

import discord

from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from discord import ApplicationContext
from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord.ext import pages
from ezcord import Bot
from ezcord import Cog

from discord.commands import guild_only
from discord.ext.commands import has_any_role

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constant_values import admin_roles
from modals import BoardKeywordModal
from trello_handler import get_trello_instance
from trello_handler import no_trello_error_msg
from views import SetTrelloBoardListToCreateCardView
from views import SetTrelloTargetListView
from views import SetTrelloUserIdView

class Configuration(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.bot = bot

    config_cmd = SlashCommandGroup("configure", "Configuration Commands")
    conf_db = config_cmd.create_subgroup("database", "Database Configurations")
    conf_tl = config_cmd.create_subgroup("trello", "Trello Configurations")

    @conf_db.command(
        name="guild_members",
        description="Update all member and with IDs in the guild"
    )
    @guild_only()
    @has_any_role(*admin_roles)
    async def conf_db_guild_members(self, ctx: ApplicationContext) -> None:
        await self.bot.db.configure_guild_members(ctx)
        await ctx.invoke(self.bot.get_command('db get members'))

    @conf_tl.command(
        name="key_token", description="Set Trello key and token"
    )
    @guild_only()
    @has_any_role(*admin_roles)
    async def configure_trello(
            self, ctx: ApplicationContext, key: str, token: str) -> None:
        await ctx.defer()
        if key and token:
            is_updated = await self.bot.db.set_trello_key_token(ctx.guild_id, key, token)
            if is_updated:
                await emb.success(ctx, "Trello key and token updated.")
                self.bot.trello.remove_client(ctx.guild_id)

    @conf_tl.command(
        name="member", description="Connect Trello members to Discord membeds"
    )
    @guild_only()
    @has_any_role(*admin_roles)
    async def connect_trello_member(self, ctx: ApplicationContext) -> None:
        await ctx.defer()
        trello = await get_trello_instance(self, ctx)

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

    @conf_tl.command(
        name="list_to_trace", description="Set interested Trello lists"
    )
    @guild_only()
    @has_any_role(*admin_roles)
    async def set_trello_intersted_lists(self, ctx: ApplicationContext) -> None:
        await ctx.defer()
        trello = await get_trello_instance(self, ctx)
        if trello is None: return

        board_list_data = await self.bot.trello.get_board_list_data(ctx.guild_id)
        trello_settings = await self.bot.db.get_trello_settings(ctx.guild_id)

        view = SetTrelloTargetListView(ctx, board_list_data, trello_settings, self.bot.db)
        await ctx.followup.send("用下拉選單設定追蹤的看板", view=view, embed=view.embed)

    @conf_tl.command(
        name="board_entry", description="Set Trello list as board entry"
    )
    @guild_only()
    @has_any_role(*admin_roles)
    async def set_trello_board_entry(self, ctx: ApplicationContext) -> None:
        await ctx.defer()
        trello = await get_trello_instance(self, ctx)
        if trello is None: return

        board_list_data = await self.bot.trello.get_board_list_data(ctx.guild_id)
        trello_settings = await self.bot.db.get_trello_settings(ctx.guild_id)

        view = SetTrelloBoardListToCreateCardView(ctx, board_list_data, trello_settings, self.bot.db)
        await ctx.followup.send("用下拉選單設定新增卡片的位置", view=view, embed=view.embed)

    @conf_tl.command(
        name="board_keywords", description="Set Trello board keywords"
    )
    @guild_only()
    @has_any_role(*admin_roles)
    async def set_board_keywords(self, ctx: ApplicationContext) -> None:
        trello = await get_trello_instance(self, ctx)
        if trello is None: return

        board_list_data = await self.bot.trello.get_board_list_data(ctx.guild_id)
        trello_settings = await self.bot.db.get_trello_settings(ctx.guild_id)

        modal = BoardKeywordModal(ctx, board_list_data, trello_settings, self.bot.db)
        await ctx.send_modal(modal)


def setup(bot: Bot):
    bot.add_cog(Configuration(bot))