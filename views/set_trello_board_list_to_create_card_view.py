import discord
import os
import sys

from discord import ApplicationContext
from discord import ButtonStyle
from discord import SelectOption
from discord.ui import Button
from discord.ui import Select
from discord.ui import View
from ezcord.internal.dc import discord as dc
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_handler import TaskOrcDB
from database_handler import TrelloSettings
from trello_handler import BoardListData
from trello_handler import TrelloHandler


class SetTrelloBoardListToCreateCardView(View):
    def __init__(
            self,
            ctx: ApplicationContext,
            board_list_data: BoardListData,
            trello_settings: TrelloSettings,
            data: TaskOrcDB):
        super().__init__()
        self.ctx = ctx
        self.board_list_data = board_list_data
        self.trello_settings = trello_settings
        self.data = data

        for bn, list_names in board_list_data.board_name_to_list_name.items():
            options = []
            bid = board_list_data.board_name_to_id[bn]
            if bid in trello_settings.board_id_list_id_to_create_card.keys():
                default_lid = trello_settings.board_id_list_id_to_create_card[bid]
                default_ln = board_list_data.list_id_to_name[default_lid]
            else:
                default_ln = ""
            for ln in list_names:
                if ln in self.trello_settings.list_name_not_to_trace: continue
                lid = board_list_data.list_name_to_id[ln]
                options.append(SelectOption(
                    label = ln,
                    value = lid,
                    default = ln == default_ln
                ))
            select = Select(
                placeholder = bn,
                options = options,
                custom_id = bid,
            )
            self.add_item(select)

        self.embed = dc.Embed(
            title = "新增卡片在看板的清單:",
            color=dc.Colour.fuchsia()
        )

        self.set_visualization()

        self.is_set_button = Button(
            label="完成！",
            custom_id="is_set_button",
            style=ButtonStyle.primary
        )
        self.add_item(self.is_set_button)

    def set_visualization(self):
        self.embed.clear_fields()
        for bid, lid in self.trello_settings.board_id_list_id_to_create_card.items():
            bn = self.board_list_data.board_id_to_name[bid]
            ln = self.board_list_data.list_id_to_name[lid]
            self.embed.add_field(name="", value=f"{bn}: {ln}", inline=False)

    async def interaction_check(self, interaction):
        if interaction.custom_id != "is_set_button":
            await self.on_select(interaction)
            return True
        else:
            self.disable_all_items()
            await self.data.set_trello_board_id_list_id_to_create_card(
                self.ctx.guild_id,
                self.trello_settings.board_id_list_id_to_create_card)
            self.embed.color=dc.Colour.green()
            self.set_visualization()
            await interaction.response.edit_message(
                content=f"完成設定！",
                view=self, embed=self.embed)

    async def on_select(self, interaction):
        bid = interaction.data["custom_id"]
        lid = interaction.data["values"][0]
        self.trello_settings.board_id_list_id_to_create_card[bid] = lid
        self.set_visualization()
        await interaction.response.edit_message(embed=self.embed, view=self)
