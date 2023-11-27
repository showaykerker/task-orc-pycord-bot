import discord
import json
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

class SetTrelloInterestedListView(View):
    def __init__(
            self,
            ctx: ApplicationContext,
            board_list_data: BoardListData,
            trello_settings: TrelloSettings,
            data: TaskOrcDB):
        super().__init__()
        self.prefix = "set_trello_intersted_lists_view_"
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
            custom_id = f"{self.prefix}select_target"
        )

        self.add_item(select)

        self.embed = dc.Embed(
            title = "追蹤清單:",
            color=dc.Colour.fuchsia()
        )
        self.set_visualization(
            set(self.board_list_data.list_name_to_id.keys()) -\
            set(self.trello_settings.list_name_not_to_trace))

    async def interaction_check(self, interaction, from_paginator=False):
        if interaction.custom_id.endswith("select_target"):
            await self.on_select(interaction)
            self.disable_all_items()
            await self.data.set_trello_traced_list_name_not_to_trace(
                self.ctx.guild_id,
                self.trello_settings.list_name_not_to_trace)
            self.embed.color=dc.Colour.green()
            if not from_paginator:
                await interaction.response.edit_message(
                    content=f"Traced List Set.",
                    view=self, embed=self.embed)
            else:
                return self.embed

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
