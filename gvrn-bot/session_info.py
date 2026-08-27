import os

import discord
from discord.ext import commands

COLOR = 0xD3E6FF

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
            image_embed = discord.Embed(color=COLOR)
            image_embed.set_image(url=SESSION_INFO_IMAGE_URL)
            image_embed.set_footer(text="GVRN Session Info Image")
            await channel.send(embed=image_embed)

        embed = discord.Embed(
            title="Greenville Roleplay Network — Roleplay 1",
            description=(
                "> • Welcome to **Greenville Roleplay Network - Roleplay 1**. Within this channel, "
                "**Greenville Roleplay Network** Staff Members will host sessions. Before joining a "
                "session, ensure to read over community-information.\n\n"
                "**Before Joining Sessions:**\n"
                "› Ensure to register your vehicles within **/vehicle-registeration**.\n"
                "› Head to support channels if assistance is needed.\n"
                "› Follow all server and session rules.\n"
                "› Listen to staff instructions at all times."
            ),
            color=COLOR,
        )
        embed.set_footer(text="Greenville Roleplay Network")

        await channel.send(embed=embed, view=SessionInfoView())

        if ctx.channel.id != channel.id:
            await ctx.reply(f"Session info sent in {channel.mention}.", mention_author=False)


async def setup(bot):
    await bot.add_cog(SessionInfo(bot))
