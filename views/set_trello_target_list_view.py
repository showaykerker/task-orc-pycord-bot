from typing import Union, List, Optional, Dict, Tuple
import os
import sys
import json
import discord
from discord import ButtonStyle
from discord.ui import View, Select, Button
from discord import SelectOption
from ezcord.internal.dc import discord as dc
from table2ascii import table2ascii as t2a
from table2ascii import PresetStyle
from discord import ApplicationContext

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trello_handler import TrelloHandler, BoardListData
from database_handler import TaskOrcDB, TrelloSettings

class SetTrelloTargetListView(View):
    def __init__(
            self,
            ctx: ApplicationContext,
            board_list_data: BoardListData,
            trello_settings: TrelloSettings,
            data: TaskOrcDB):
        super().__init__()
        self.ctx = ctx
        self.data = data

        # self.board_list_data = trello.get_board_list_data()
        # self.trello_settings = data.get_trello_settings()
        self.board_list_data = board_list_data
        self.trello_settings = trello_settings

        self.trello_list_id_to_name = {}

        options = []

        for b, ls in self.board_list_data.board_name_to_list_name.items():
            for l in ls:
                label = f"{b} - {l}"
                lid = self.board_list_data.list_name_to_id[l]
                self.trello_list_id_to_name[lid] = l
                options.append(SelectOption(
                    label = label,
                    value = lid,
                    default = lid in self.trello_settings.trello_traced_list_id
                ))

        select = Select(
            placeholder = "selected",
            options = options,
            min_values = 0,
            max_values = len(self.board_list_data),
            custom_id = "select_target"
        )

        self.is_set_button = Button(
            label = "完成",
            custom_id = "is_set_button",
            style = ButtonStyle.primary
        )
        self.add_item(select)
        self.add_item(self.is_set_button)

        self.embed = dc.Embed(
            title = "追蹤清單:",
            color=dc.Colour.fuchsia()
        )
        self.set_visualization(self.trello_settings.trello_traced_list_id)

    async def interaction_check(self, interaction):
        if interaction.custom_id == "select_target":
            await self.on_select(interaction)
        else:
            self.disable_all_items()
            await self.data.set_trello_traced_list_id(
                self.ctx.guild_id,
                self.trello_settings.trello_traced_list_id)
            self.embed.color=dc.Colour.green()
            await interaction.response.edit_message(
                content=f"Traced List Set.",
                view=self, embed=self.embed)

    def set_visualization(self, chosen_list_ids: List[str]):
        chosen_list = [self.trello_list_id_to_name[lid] for lid in set(chosen_list_ids)]
        if self.embed.fields:
            self.embed.remove_field(0)
        self.embed.add_field(
            name="",
            value=", ".join(chosen_list)
        )

    async def on_select(self, interaction):
        self.trello_settings.trello_traced_list_id = interaction.data["values"]
        self.set_visualization(self.trello_settings.trello_traced_list_id)
        await interaction.response.edit_message(embed=self.embed)
