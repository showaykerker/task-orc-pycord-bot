import copy
import discord

from typing import Callable
from typing import Dict

from discord import ApplicationContext
from discord import ButtonStyle
from discord.ui import Button
from discord.ui import Select
from discord.ui import View
from ezcord.internal.dc import discord as dc
from table2ascii import PresetStyle
from table2ascii import table2ascii as t2a

def dict_to_ascii_table(discord_name_to_trello_name: dict) -> str:
    fields = ["Discord Name", "Trello Name"]

    # Trim name length
    body = [[k[:20], v[:20]] for k, v in discord_name_to_trello_name.items()]

    table = t2a(
        header = fields,
        body = body,
        style = PresetStyle.simple,
        cell_padding=1,
        use_wcwidth=True,
    )
    return f"```\n{table}\n```"

class SetTrelloUserIdView(View):
    MAX_PER_PAGE = 4
    def __init__(
            self,
            ctx: ApplicationContext,
            members_in_guild_to_be_assigned: Dict[str, str],  # {discord_name: discord_id}
            trello_id_to_name_dict: Dict[str, str],  # {trello_id: trello_name}
            is_set_callback: Callable[str, str],  # func(discord_id, trello_id) update trello_id in database
            discord_name_to_trello_name_dict: Dict[str, str]={}) -> None:  # {discord_name: trello_name}
        super().__init__()
        self.to_be_assigned = copy.deepcopy(members_in_guild_to_be_assigned)
        self.candidate = copy.deepcopy(members_in_guild_to_be_assigned)
        self.options = trello_id_to_name_dict
        self.is_set_callback = is_set_callback
        self.embed = dc.Embed(
            title = "名稱對照:",
            color=dc.Colour.fuchsia()
        )
        self.selected_item_to_embed_field_id = {}
        self.results_discord_name_to_trello_id = {}
        self.results_discord_name_to_trello_name = discord_name_to_trello_name_dict
        self.is_set_button = Button(
            label="設定下一批！",
            custom_id="is_set_button",
            style=ButtonStyle.primary
        )
        self.update_view()


    def update_view(self):
        if len(self.to_be_assigned) == 0: return

        self.clear_items()

        keys_to_be_remove = []
        for i, (discord_name, discord_id) in enumerate(self.to_be_assigned.items()):
            select = Select(
                placeholder=f"{discord_name}",
                options=[
                    discord.SelectOption(
                        label=name,
                        value=member_id
                    ) for member_id, name in self.options.items()
                ]
            )
            select.custom_id = discord_name
            self.add_item(select)
            keys_to_be_remove.append(discord_name)
            if i == self.MAX_PER_PAGE - 1:
                break

        [self.to_be_assigned.pop(k) for k in keys_to_be_remove]

        if self.results_discord_name_to_trello_name:
            self.embed.clear_fields()
            self.embed.add_field(
                name="",
                value=dict_to_ascii_table(self.results_discord_name_to_trello_name)
            )

        if len(self.to_be_assigned) == 0:
            self.is_set_button.label="完成！"
        self.add_item(self.is_set_button)
        self.embed.set_footer(text=f"剩餘{len(self.to_be_assigned)}人未設定")
        self.embed.color=dc.Colour.fuchsia()


    async def interaction_check(self, interaction):
        if interaction.custom_id != "is_set_button":
            await self.on_select(interaction)
            return True
        else:
            actually_set = []
            for discord_name, trello_id in self.results_discord_name_to_trello_id.items():
                discord_id = self.candidate[discord_name]
                if trello_id:
                    await self.is_set_callback(discord_id, trello_id)
                    actually_set.append(discord_name)
            actually_set_verbose = ", ".join(actually_set)
            if self.is_set_button.label == "完成！":
                self.disable_all_items()
                self.embed.color=dc.Colour.green()
                await interaction.response.edit_message(content="設定完成！", view=self, embed=self.embed)
            else:
                self.update_view()
                await interaction.response.edit_message(view=self, embed=self.embed)

    async def on_select(self, interaction):
        trello_id = interaction.data["values"][0]
        discord_name = interaction.data["custom_id"]
        trello_name = self.options.get(trello_id)

        self.results_discord_name_to_trello_id[discord_name] = trello_id
        self.results_discord_name_to_trello_name[discord_name] = trello_name
        self.embed.clear_fields()
        self.embed.add_field(
            name="",
            value=dict_to_ascii_table(self.results_discord_name_to_trello_name)
        )
        await interaction.response.edit_message(embed=self.embed)
