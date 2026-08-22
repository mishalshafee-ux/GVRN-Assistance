import os

import discord
from discord.ext import commands

COLOR = 0x76F55D
SUGGESTION_CHANNEL_ID = int(os.getenv("SUGGESTION_CHANNEL_ID", "0"))


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

    @commands.command(name="suggest")
    async def suggest(self, ctx, *, suggestion: str = None):
        if not suggestion:
            await ctx.reply("Usage: `!suggest your idea here`", mention_author=False)
            return

        channel = ctx.guild.get_channel(SUGGESTION_CHANNEL_ID)

        if not isinstance(channel, discord.TextChannel):
            await ctx.reply("Suggestion channel is not set correctly.", mention_author=False)
            return

        embed = discord.Embed(
            title="New Suggestion",
            description=suggestion,
            color=COLOR,
        )
        embed.add_field(name="Suggested By", value=ctx.author.mention, inline=False)
        embed.set_footer(text=f"User ID: {ctx.author.id}")

        message = await channel.send(embed=embed, view=SuggestionVoteView())
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        await ctx.reply(f"Your suggestion was sent: {message.jump_url}", mention_author=False)


async def setup(bot):
    await bot.add_cog(Suggestions(bot))
