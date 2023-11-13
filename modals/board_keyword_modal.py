import os
import sys
from typing import Union, List, Optional, Dict, Tuple
import discord
from discord import ApplicationContext

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trello_handler import TrelloHandler, BoardListData
from database_handler import TaskOrcDB, TrelloSettings

class BoardKeywordModal(discord.ui.Modal):
    def __init__(
            self,
            ctx: ApplicationContext,
            board_list_data: BoardListData,
            trello_settings: TrelloSettings,
            data: TaskOrcDB) -> None:
        super().__init__(title="設定將任務分類到看板的關鍵字\n用逗號分開關鍵字\n留空作為預設看板\n'x'取消關鍵字")
        self.ctx = ctx
        self.trello_settings = trello_settings
        self.board_list_data = board_list_data
        self.data = data
        for bn, bid in board_list_data.board_name_to_id.items():
            kws = self.trello_settings.board_keywords.get(bid) or ""
            self.add_item(discord.ui.InputText(
                label=bn,
                placeholder=kws,
                required=False,
                custom_id=bid,
                style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Modal Results")
        self.trello_settings.board_keywords.clear()
        for child in self.children:
            kws = child.value
            if child.value == "" and child.placeholder != "":
                kws = child.placeholder

            self.trello_settings.board_keywords[child.custom_id] = \
                kws.replace("，", ",").replace(";", ",").replace("；", ",").replace(" ", "").replace("　", "")
            self.trello_settings.board_keywords[child.custom_id].strip()
            try:
                if self.trello_settings.board_keywords[child.custom_id][-1] == ",":
                    self.trello_settings.board_keywords[child.custom_id] = self.trello_settings.board_keywords[child.custom_id][:-1]
            except IndexError:
                pass
            kws = self.trello_settings.board_keywords[child.custom_id].split(",")
            kws_handled = []
            for i, kw in enumerate(kws):
                if kw.strip():
                    try:
                        kws_handled.append(kw.lower())
                    except:
                        kws_hanlded.append(kw)
            self.trello_settings.board_keywords[child.custom_id] = ",".join(kws_handled)
            embed.add_field(
                name=self.board_list_data.board_id_to_name[child.custom_id],
                value=self.trello_settings.board_keywords[child.custom_id])
        await self.data.set_trello_board_id_keywords(
            self.ctx.guild_id,
            self.trello_settings.board_keywords)
        await interaction.response.send_message(embeds=[embed])