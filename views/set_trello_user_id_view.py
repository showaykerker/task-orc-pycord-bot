import discord
from discord import ButtonStyle
from discord.ui import View, Select, Button
from ezcord.internal.dc import discord as dc
from table2ascii import table2ascii as t2a
from table2ascii import PresetStyle

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
    def __init__(
            self,
            ctx,
            members_in_guild_to_be_assigned,
            trello_id_to_name_dict,
            is_set_callback,
            discord_name_to_trello_name_dict={}):
        super().__init__()
        self.to_be_assigned = members_in_guild_to_be_assigned
        self.options = trello_id_to_name_dict
        self.is_set_callback = is_set_callback

        for member_discord_name, member_discord_id in self.to_be_assigned.items():
            select = Select(
                placeholder=f"{member_discord_name}",
                options=[discord.SelectOption(label=name, value=member_id) for member_id, name in self.options.items()]
            )
            select.custom_id = member_discord_name
            self.add_item(select)

        self.embed = dc.Embed(
            title = "Result:",
            color=dc.Colour.fuchsia()
        )

        self.selected_item_to_embed_field_id = {}
        self.results_discord_name_to_trello_id = {}
        self.results_discord_name_to_trello_name = discord_name_to_trello_name_dict

        if discord_name_to_trello_name_dict:
            self.embed.add_field(
                name="",
                value=dict_to_ascii_table(self.results_discord_name_to_trello_name)
            )

        self.is_set_button = Button(
            label="Is Set",
            custom_id="is_set_button",
            style=ButtonStyle.primary
        )
        self.add_item(self.is_set_button)

    async def interaction_check(self, interaction):
        if interaction.custom_id != "is_set_button":
            await self.on_select(interaction)
            return True
        else:
            actually_set = []
            for discord_name, trello_id in self.results_discord_name_to_trello_id.items():
                discord_id = self.to_be_assigned[discord_name]
                if trello_id:
                    await self.is_set_callback(discord_id, trello_id)
                    actually_set.append(discord_name)
            actually_set_verbose = ", ".join(actually_set)
            self.disable_all_items()
            self.embed.color=dc.Colour.green()
            await interaction.response.edit_message(
                content=f"Set trello ID for member {actually_set_verbose}",
                view=self, embed=self.embed)

    async def on_select(self, interaction):
        trello_id = interaction.data["values"][0]
        discord_name = interaction.data["custom_id"]
        trello_name = self.options.get(trello_id)

        self.results_discord_name_to_trello_id[discord_name] = trello_id
        self.results_discord_name_to_trello_name[discord_name] = trello_name
        if self.embed.fields:
            self.embed.remove_field(0)
        self.embed.add_field(
            name="",
            value=dict_to_ascii_table(self.results_discord_name_to_trello_name)
        )
        await interaction.response.edit_message(embed=self.embed)
