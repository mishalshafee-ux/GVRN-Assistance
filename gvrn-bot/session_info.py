import os

import discord
from discord.ext import commands

SESSION_INFO_CHANNEL_ID = int(os.getenv("SESSION_INFO_CHANNEL_ID", "0"))
SERVER_PERKS_URL = os.getenv("SERVER_PERKS_URL", "")

SESSION_INFO_COLOR = 0x76F55D
SESSION_INFO_TITLE = "Greenville Roleplay Network — Roleplay"


def build_session_info_embed():
    embed = discord.Embed(
        description=(
            f"❤ **{SESSION_INFO_TITLE}** ❤\n\n"
            f"▬ Welcome to **Greenville Roleplay Network**! Within this channel, "
            f"GVRN Staff Members will host sessions. Before joining a session, "
            f"ensure to read over our community information.\n\n"
            f"**Before Joining Sessions:**\n"
            f"› Ensure to register your vehicles within **/vehicle-registeration**.\n"
            f"› Head to support channels if assistance is needed.\n"
            f"› Follow all server rules and roleplay guidelines."
        ),
        color=SESSION_INFO_COLOR,
    )
    embed.set_footer(text="Greenville Roleplay Network")
    return embed


class SessionInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sessioninfo")
    @commands.has_permissions(administrator=True)
    async def sessioninfo(self, ctx):
        channel = ctx.guild.get_channel(SESSION_INFO_CHANNEL_ID) if SESSION_INFO_CHANNEL_ID else ctx.channel

        if not isinstance(channel, discord.TextChannel):
            await ctx.send("Session info channel not found. Check SESSION_INFO_CHANNEL_ID.")
            return

        view = discord.ui.View(timeout=None)

        if SERVER_PERKS_URL:
            view.add_item(
                discord.ui.Button(
                    label="Purchase Server Perks",
                    style=discord.ButtonStyle.link,
                    url=SERVER_PERKS_URL,
                )
            )

        await channel.send(embed=build_session_info_embed(), view=view)

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass


async def setup(bot):
    await bot.add_cog(SessionInfo(bot))
