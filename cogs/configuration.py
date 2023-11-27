import os
import sys
import asyncio

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
from ezcord import emb
from ezcord.internal.dc import discord as dc

from discord.commands import guild_only
from discord.ext.commands import has_any_role

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constant_values import admin_roles
from trello_handler import get_trello_instance
from trello_handler import no_trello_error_msg
from trello_handler import TrelloHandler
from trello_handler import BoardListData
from database_handler import TrelloSettings
# from views import ConfigurationPaginator
from views import SetTrelloBoardEntryView
from views import SetTrelloInterestedListView
from views import SetTrelloUserIdView
from modals import BoardKeywordModal

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
        name="key_token", description="設定 Trello 的密鑰和權杖"
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
            else:
                await get_trello_instance(self, ctx)
                await emb.success(ctx, "Trello key and token set.")


    @conf_tl.command(
        name="member", description="設定 Trello 帳號對應的 Discord 成員"
    )
    @guild_only()
    @has_any_role(*admin_roles)
    async def connect_trello_member(self, ctx: ApplicationContext) -> None:
        await ctx.defer()
        view = await self._get_set_trello_user_id_view(ctx)
        await ctx.followup.send("用下拉選單設定成員名稱對照", view=view, embed=view.embed)

    @conf_tl.command(
        name="list_to_trace", description="設定要追蹤的 Trello 看板"
    )
    @guild_only()
    @has_any_role(*admin_roles)
    async def set_trello_intersted_lists(self, ctx: ApplicationContext) -> None:
        await ctx.defer()
        view = await self._get_set_trello_intersted_lists_view(ctx)
        await ctx.followup.send("用下拉選單設定追蹤的看板", view=view, embed=view.embed)

    @conf_tl.command(
        name="board_entry", description="設定用來新增卡片的 Trello 清單"
    )
    @guild_only()
    @has_any_role(*admin_roles)
    async def set_trello_board_entry(self, ctx: ApplicationContext) -> None:
        await ctx.defer()
        view = await self._get_set_trello_board_list_to_create_card_view(ctx)
        await ctx.followup.send("用下拉選單設定新增卡片的位置", view=view, embed=view.embed)

    @conf_tl.command(
        name="board_keywords", description="設定 Trello 看板關鍵字"
    )
    @guild_only()
    @has_any_role(*admin_roles)
    async def set_board_keywords(self, ctx: ApplicationContext) -> None:
        modal = await self._get_board_keyword_modal(ctx)
        await ctx.send_modal(modal)

    async def _get_set_trello_user_id_view(
            self,
            ctx: ApplicationContext,
            trello: Optional[TrelloHandler] = None) -> SetTrelloUserIdView:
        trello = trello or await get_trello_instance(self, ctx)
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
        return SetTrelloUserIdView(
            ctx,
            members_in_guild_to_be_assigned,
            trello_id_to_name_dict,
            is_set_callback,
            discord_name_to_trello_name_dict)


    async def _get_set_trello_intersted_lists_view(
            self,
            ctx: ApplicationContext,
            trello: Optional[TrelloHandler] = None,
            board_list_data: Optional[BoardListData] = None,
            trello_settings: Optional[TrelloSettings] = None) -> SetTrelloInterestedListView:
        trello = trello or await get_trello_instance(self, ctx)
        if trello is None: return
        board_list_data = board_list_data or await self.bot.trello.get_board_list_data(ctx.guild_id)
        trello_settings = trello_settings or await self.bot.db.get_trello_settings(ctx.guild_id)
        return SetTrelloInterestedListView(ctx, board_list_data, trello_settings, self.bot.db)

    async def _get_set_trello_board_list_to_create_card_view(
            self,
            ctx: ApplicationContext,
            trello: Optional[TrelloHandler] = None,
            board_list_data: Optional[BoardListData] = None,
            trello_settings: Optional[TrelloSettings] = None) -> SetTrelloBoardEntryView:
        trello = trello or await get_trello_instance(self, ctx)
        if trello is None: return
        board_list_data = board_list_data or await self.bot.trello.get_board_list_data(ctx.guild_id)
        trello_settings = trello_settings or await self.bot.db.get_trello_settings(ctx.guild_id)
        return SetTrelloBoardEntryView(ctx, board_list_data, trello_settings, self.bot.db)

    async def _get_board_keyword_modal(
            self,
            ctx: ApplicationContext,
            trello: Optional[TrelloHandler] = None,
            board_list_data: Optional[BoardListData] = None,
            trello_settings: Optional[TrelloSettings] = None) -> BoardKeywordModal:
        trello = trello or await get_trello_instance(self, ctx)
        if trello is None: return
        board_list_data = board_list_data or await self.bot.trello.get_board_list_data(ctx.guild_id)
        trello_settings = trello_settings or await self.bot.db.get_trello_settings(ctx.guild_id)
        return BoardKeywordModal(ctx, board_list_data, trello_settings, self.bot.db)


def setup(bot: Bot):
    bot.add_cog(Configuration(bot))