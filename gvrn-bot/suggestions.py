import os

import discord
from discord import app_commands
from discord.ext import commands

COLOR = 0xE7F6FF
SUGGESTION_CHANNEL_ID = int(os.getenv("SUGGESTION_CHANNEL_ID", "0") or 0)


class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="suggest", description="Send a suggestion.")
    @app_commands.describe(suggestion="Your suggestion idea")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        channel = interaction.guild.get_channel(SUGGESTION_CHANNEL_ID)

        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Suggestion channel is not set correctly.", ephemeral=True)
            return

        embed = discord.Embed(
            title="New Suggestion",
            description=suggestion,
            color=COLOR,
        )
        embed.add_field(name="Suggested By", value=interaction.user.mention, inline=False)
        embed.set_footer(text=f"User ID: {interaction.user.id}")

        message = await channel.send(embed=embed)

        await interaction.response.send_message(f"Your suggestion was sent: {message.jump_url}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Suggestions(bot))
