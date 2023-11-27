import os
import sys

from discord import ApplicationContext
from discord import Interaction
from discord.ui import Button
from discord.ui import Select
from discord.ui import View
from ezcord.internal.dc import discord as dc

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_handler import TaskOrcDB
from database_handler import TrelloSettings
from trello_handler import BoardListData

class ConfigurationBaseView(View):
    def __init__(
            self,
            name: str,
            ctx: ApplicationContext,
            board_list_data: BoardListData,
            trello_settings: TrelloSettings,
            data: TaskOrcDB):
        super().__init__()
        self.prefix = f"{name}"
        self.ctx = ctx
        self.data = data
        self.board_list_data = board_list_data
        self.trello_settings = trello_settings
        self.embed = dc.Embed(title="Configs", color=dc.Colour.fuchsia())
        self.confirm_button = Button(
            label="完成！",
            custom_id=f"{self.prefix}_confirm_button",
            style=ButtonStyle.primary)
        self.next_batch_button = Button(
            label="下一批！",
            custom_id=f"{self.prefix}_next_batch_button",
            style=ButtonStyle.secondary)
        self.last_batch_button = Button(
            label="上一批！",
            custom_id=f"{self.prefix}_last_batch_button",
            style=ButtonStyle.secondary)
        self.next_config_button = Button(
            label="下一個設定！",
            custom_id=f"{self.prefix}_next_config_button",
            style=ButtonStyle.secondary)
        self.last_config_button = Button(
            label="上一個設定！",
            custom_id=f"{self.prefix}_last_config_button",
            style=ButtonStyle.secondary)

    def set_embed_title(self, title: str) -> None:
        self.embed.title = title

    def set_embed_description(self, description: str) -> None:
        self.embed.description = description

    def set_embed_footer(self, footer: str) -> None:
        self.embed.footer = footer

    def set_button(self, single_config: bool=True) -> None:
        self.add_item(self.last_batch_button)
        self.add_item(self.confirm_button)
        self.add_item(self.next_batch_button)

    async def confirm(self, interaction: Interaction):
        """
        Called when confirm button is clicked
        """
        pass

