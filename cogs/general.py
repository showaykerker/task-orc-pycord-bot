import inspect
import random

from itertools import cycle

from discord import ApplicationContext
from ezcord import Bot
from ezcord import Cog
from ezcord import emb
from ezcord.internal.dc import discord as dc


class General(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)

    @dc.slash_command(
        name="ping", description="Check if the bot is alive")
    async def ping(self, ctx: ApplicationContext) -> None:
        """
        Check if the bot is alive.

        :param ctx: The ApplicationContext.
        """
        msg = f"🏓 Pong!\nThe bot latency is {round(self.bot.latency * 1000)}ms."
        await emb.success(ctx, msg)


def setup(bot: Bot):
    bot.add_cog(General(bot))
