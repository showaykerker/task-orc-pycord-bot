from typing import Union, List, Optional, Dict, Tuple
import os
import sys
import json
import discord
from discord import ButtonStyle
from discord.ui import View, Select, Button
from discord import SelectOption
from ezcord.internal.dc import discord as dc
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

        self.board_list_data = board_list_data
        self.trello_settings = trello_settings

        self.trello_list_id_to_name = {}
        self.trello_list_name_to_trace = \
            set(self.board_list_data.list_name_to_id.keys()) - set(self.trello_settings.list_name_not_to_trace)

        options = []

        for b, ls in self.board_list_data.board_name_to_list_name.items():
            for l in ls:
                label = f"{b} - {l}"
                lid = self.board_list_data.list_name_to_id[l]
                self.trello_list_id_to_name[lid] = l
                options.append(SelectOption(
                    label = label,
                    value = l,
                    default = l not in self.trello_settings.list_name_not_to_trace
                ))

        select = Select(
            placeholder = "selected",
            options = options,
            min_values = 0,
            max_values = len(self.board_list_data),
            custom_id = "select_target"
        )

        # self.is_set_button = Button(
        #     label = "完成",
        #     custom_id = "is_set_button",
        #     style = ButtonStyle.primary
        # )
        self.add_item(select)
        # self.add_item(self.is_set_button)

        self.embed = dc.Embed(
            title = "追蹤清單:",
            color=dc.Colour.fuchsia()
        )
        self.set_visualization(
            set(self.board_list_data.list_name_to_id.keys()) -\
            set(self.trello_settings.list_name_not_to_trace))

    async def interaction_check(self, interaction):
        if interaction.custom_id == "select_target":
            await self.on_select(interaction)
            self.disable_all_items()
            await self.data.set_trello_traced_list_name_not_to_trace(
                self.ctx.guild_id,
                self.trello_settings.list_name_not_to_trace)
            self.embed.color=dc.Colour.green()
            await interaction.response.edit_message(
                content=f"Traced List Set.",
                view=self, embed=self.embed)

    def set_visualization(self, chosen_list_names: List[str]):
        if self.embed.fields:
            self.embed.remove_field(0)
        self.embed.add_field(
            name="",
            value=", ".join(chosen_list_names)
        )

    async def on_select(self, interaction):
        trello_traced_list_id = interaction.data["values"]
        self.trello_settings.list_name_not_to_trace =\
            set(self.board_list_data.list_name_to_id.keys()) -\
            set(trello_traced_list_id)
        self.set_visualization(
            set(self.board_list_data.list_name_to_id.keys()) -\
            set(self.trello_settings.list_name_not_to_trace))
        # await interaction.response.edit_message(embed=self.embed, view=self)
