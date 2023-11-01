import inspect
import random
from itertools import cycle

from ezcord.internal.dc import discord as dc
from ezcord import Bot, Cog


class Template(Cog, hidden=True):
    def __init__(self, bot: Bot):
        super().__init__(bot)

    @dc.slash_command(
        name="template_slash_cmd_name", description="template slash cmd desc."
    )
    async def command_name(self, ctx) -> None:
        await ctx.send("hi")


def setup(bot: Bot):
    # Uncomment the following line to install this cog.
    # bot.add_cog(Template(bot))
    pass
