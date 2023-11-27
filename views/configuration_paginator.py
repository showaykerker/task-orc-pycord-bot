from typing import Dict
from typing import Union

from discord import ButtonStyle
from discord.ext import pages
from discord.ui import Button
from ezcord.internal.dc import discord as dc

class ViewData:
    def __init__(self, name, content, custom_view):
        self.name = name
        self.content = content
        self.view = custom_view
        self.interaction_check = self.view.interaction_check
    def get_page_dict(self):
        return {
            "content": self.content,
            "custom_view": self.view
        }

class ConfigurationPaginator(pages.Paginator):
    def __init__(
            self,
            config_pages,
            *args, **kwargs):
        self.config_view_data = []
        page_dicts = []
        for i, p in enumerate(config_pages):
            view_data = ViewData(**p)
            self.config_view_data.append(view_data)
            if i != len(config_pages) - 1:
                if hasattr(view_data.view, "is_set_button"):
                    view_data.view.is_set_button.label = "下一個設定"
            if not hasattr(view_data.view, "is_set_button"):
                view_data.view.add_item(Button(
                    label="下一個設定",
                    custom_id=f"{view_data.view.prefix}is_set_button",
                    style=ButtonStyle.primary
                ))
            page_dicts.append(view_data.get_page_dict())

        created_pages = [pages.Page(embeds=[v["custom_view"].embed], **v) for v in page_dicts]
        super().__init__(pages=created_pages, use_default_buttons=False, show_indicator=False, *args, **kwargs)

    async def interaction_check(self, interaction: dc.Interaction):
        print(interaction.custom_id)
        for d in self.config_view_data:
            if interaction.custom_id.startswith(d.name):
                print("paginator interaction check")
                await d.interaction_check(interaction, from_paginator=True)
                d.view.clear_items()
                self.update_custom_view(d.view)
        if interaction.custom_id.endswith("_is_set_button"):
            page_content = self.pages[(self.current_page+1) % (self.page_count+1)]
            self.goto_page((self.current_page+1) % (self.page_count+1))
        #     await self.message.edit(embed=page_content.custom_view.embed, view=page_content.custom_view)
            await interaction.response.edit_message(content=page_content.content, embeds=page_content.embeds)
        #     print("end")
        #     return True
        # else:
        #     page_content = self.pages[self.current_page]
        #     # await self.message.edit(embed=page_content.custom_view.embed, view=page_content.custom_view)
        #     await interaction.response.edit_message(content=page_content.content, embeds=page_content.embeds)
        #     print("hey")
        #     return True
