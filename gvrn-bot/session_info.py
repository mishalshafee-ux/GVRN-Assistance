import os

import discord
from discord.ext import commands

COLOR = 0x76F55D

SESSION_INFO_CHANNEL_ID = int(os.getenv("SESSION_INFO_CHANNEL_ID", "0") or 0)
SESSION_INFO_IMAGE_URL = os.getenv("SESSION_INFO_IMAGE_URL", "")
SERVER_PERKS_URL = os.getenv("SERVER_PERKS_URL", "")


class SessionInfoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        if SERVER_PERKS_URL:
            self.add_item(
                discord.ui.Button(
                    label="Purchase Server Perks",
                    style=discord.ButtonStyle.link,
                    url=SERVER_PERKS_URL,
                )
            )


class SessionInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(SessionInfoView())

    @commands.command(name="sessioninfo")
    @commands.has_permissions(manage_messages=True)
    async def session_info(self, ctx):
        channel = ctx.guild.get_channel(SESSION_INFO_CHANNEL_ID) if SESSION_INFO_CHANNEL_ID else ctx.channel

        if not isinstance(channel, discord.TextChannel):
            await ctx.reply("Session info channel is not set correctly.", mention_author=False)
            return

        if SESSION_INFO_IMAGE_URL:
            await channel.send(SESSION_INFO_IMAGE_URL)

        embed = discord.Embed(
            title="💕 Greenville Roleplay Network — Roleplay Information 💕",
            description=(
                "> Welcome to **Greenville Roleplay Network**. Within this channel, staff members "
                "will host sessions for the community.\n\n"
                "> Before joining a session, please make sure you read all session information carefully "
                "and follow all server rules.\n\n"
                "**Before Joining Sessions:**\n\n"
                "› Register your vehicle in **/vehicle-registeration**.\n\n"
                "› Head to support channels if assistance is needed.\n\n"
                "› Follow staff instructions during all sessions.\n\n"
                "› Keep roleplay realistic, respectful, and organized.\n\n"
                "**Session Reminder:**\n\n"
                "> Failure to follow session rules may result in moderation action."
            ),
            color=COLOR,
        )
        embed.set_footer(text="GVRN Session Information")

        await channel.send(embed=embed, view=SessionInfoView())

        if ctx.channel.id != channel.id:
            await ctx.reply(f"Session info sent in {channel.mention}.", mention_author=False)


async def setup(bot):
    await bot.add_cog(SessionInfo(bot))
