import discord
from discord import ButtonStyle
from discord.ui import View, Select, Button
from ezcord.internal.dc import discord as dc

class SetTrelloUserIdView(View):
    def __init__(self, members_in_guild_to_be_assigned, options, is_set_callback):
        super().__init__()
        self.to_be_assigned = members_in_guild_to_be_assigned
        self.options = options
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
            #         actually_set.append(discord_name)
            # actually_set_verbose = ", ".join(actually_set)
            # await interaction.send_response(f"Set trello ID for member {actually_set_verbose}")


    async def on_select(self, interaction):
        member_id = interaction.data["values"][0]
        item = interaction.data["custom_id"]
        if self.selected_item_to_embed_field_id.get(item) is not None:
            index = self.selected_item_to_embed_field_id.get(item)
            self.embed.set_field_at(index, name=item, value=member_id, inline=False)
        else:
            self.selected_item_to_embed_field_id[item] = len(self.embed.fields)
            self.embed.add_field(name=item, value=member_id, inline=False)
        self.results_discord_name_to_trello_id[item] = member_id
        await interaction.response.edit_message(embed=self.embed)
