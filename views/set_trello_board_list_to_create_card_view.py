import discord
import os
import sys

from typing import Dict

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
from table2ascii import PresetStyle
from table2ascii import table2ascii as t2a
from trello_handler import BoardListData
from trello_handler import TrelloHandler

def dict_to_ascii_table(board_name_to_list_name: Dict[str, str]) -> str:
    fields = ["Trello Board", "Trello List Entry"]

    # Trim name length
    body = [[k[:20], v[:20]] for k, v in board_name_to_list_name.items()]

    table = t2a(
        header = fields,
        body = body,
        style = PresetStyle.simple,
        cell_padding=1,
        use_wcwidth=True,
    )
    return f"```\n{table}\n```"[:1024]

class SetTrelloBoardListToCreateCardView(View):
    MAX_PER_PAGE = 4
    def __init__(
            self,
            ctx: ApplicationContext,
            board_list_data: BoardListData,
            trello_settings: TrelloSettings,
            data: TaskOrcDB):
        super().__init__()
        self.prefix = "set_trello_board_list_to_create_card_view_"
        self.ctx = ctx
        self.board_list_data = board_list_data
        self.trello_settings = trello_settings
        self.data = data

        self.embed = dc.Embed(
            title = "新增卡片在看板的清單:",
            color=dc.Colour.fuchsia()
        )

        all_boards = set(board_list_data.board_name_to_id.keys())
        boards_have_list_entry = set([
            board_list_data.board_id_to_name[bid] \
            for bid in trello_settings.board_id_list_id_to_create_card.keys()
        ])
        boards_without_list_entry = list(all_boards - boards_have_list_entry)
        boards_without_list_entry.sort()
        boards_have_list_entry = list(boards_have_list_entry)
        boards_have_list_entry.sort()

        self.all_boards_to_be_set = \
            [b for b in boards_without_list_entry] +\
            [b for b in boards_have_list_entry]

        self.get_next_batch_button = Button(
            label="設定下一批！",
            custom_id=f"{self.prefix}get_next_batch_button",
            style=ButtonStyle.secondary
        )
        self.is_set_button = Button(
            label="完成！",
            custom_id=f"{self.prefix}is_set_button",
            style=ButtonStyle.primary
        )

        self.set_embed()
        self.update_view()


    def update_view(self):
        if len(self.all_boards_to_be_set) == 0: return
        self.clear_items()

        keys_to_be_remove = []
        for i, board_name in enumerate(self.all_boards_to_be_set):
            list_names = self.board_list_data.board_name_to_list_name[board_name]
            options = []
            board_id = self.board_list_data.board_name_to_id[board_name]
            if board_id in self.trello_settings.board_id_list_id_to_create_card.keys():
                default_list_id = self.trello_settings.board_id_list_id_to_create_card[board_id]
                default_list_name = self.board_list_data.list_id_to_name[default_list_id]
            else:
                default_list_name = ""
            for list_name in list_names:
                list_id = self.board_list_data.list_name_to_id[list_name]
                options.append(SelectOption(
                    label = list_name,
                    value = list_id
                ))
            select = Select(
                placeholder = board_name,
                options = options,
                custom_id = f"{self.prefix}{board_id}",
            )

            self.add_item(select)
            keys_to_be_remove.append(board_name)
            if i == self.MAX_PER_PAGE - 1:
                break

        [self.all_boards_to_be_set.remove(k) for k in keys_to_be_remove]

        if len(self.all_boards_to_be_set) == 0:
            self.get_next_batch_button.disabled = True
        else:
            self.get_next_batch_button.disabled = False
        self.add_item(self.get_next_batch_button)
        self.add_item(self.is_set_button)
        self.embed.set_footer(text=f"剩餘{len(self.all_boards_to_be_set)}個看板")
        self.embed.color = dc.Colour.fuchsia()

    def set_embed(self):
        self.embed.clear_fields()
        board_name_to_list_name = {}
        for bid, lid in self.trello_settings.board_id_list_id_to_create_card.items():
            bn = self.board_list_data.board_id_to_name[bid]
            ln = self.board_list_data.list_id_to_name[lid]
            board_name_to_list_name[bn] = ln
        self.embed.add_field(
            name="",
            value=dict_to_ascii_table(board_name_to_list_name),
            inline=False)

    async def interaction_check(self, interaction, from_paginator=False):
        if not interaction.custom_id.endswith("button"):
            await self.on_select(interaction)
            return True
        else:
            await self.data.set_trello_board_id_list_id_to_create_card(
                self.ctx.guild_id,
                self.trello_settings.board_id_list_id_to_create_card)
            self.set_embed()
            if interaction.custom_id.endswith("is_set_button") or\
                    len(self.all_boards_to_be_set) == 0:
                self.disable_all_items()
                self.embed.color = dc.Colour.green()
                if not from_paginator:
                    await interaction.response.edit_message(
                        content=f"完成設定！",
                        view=self, embed=self.embed)
            else:
                self.update_view()
                if not from_paginator:
                    await interaction.response.edit_message(
                        view=self, embed=self.embed)

    async def on_select(self, interaction):
        if interaction.data.get("values"):
            bid = interaction.data["custom_id"].replace(self.prefix, "")
            lid = interaction.data["values"][0]
            self.trello_settings.board_id_list_id_to_create_card[bid] = lid
        self.set_embed()
        await interaction.response.edit_message(embed=self.embed, view=self)
