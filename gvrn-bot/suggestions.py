import os

import discord
from discord import app_commands
from discord.ext import commands

COLOR = 0x76F55D
SUGGESTION_CHANNEL_ID = int(os.getenv("SUGGESTION_CHANNEL_ID", "0") or 0)


class SuggestionVoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Upvote", emoji="✅", style=discord.ButtonStyle.success, custom_id="suggestion_upvote")
    async def upvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Your upvote was counted.", ephemeral=True)

    @discord.ui.button(label="Downvote", emoji="❌", style=discord.ButtonStyle.danger, custom_id="suggestion_downvote")
    async def downvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Your downvote was counted.", ephemeral=True)


class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(SuggestionVoteView())

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

        message = await channel.send(embed=embed, view=SuggestionVoteView())
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        await interaction.response.send_message(f"Your suggestion was sent: {message.jump_url}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Suggestions(bot))
