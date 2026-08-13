import os

import discord
from discord import app_commands
from discord.ext import commands

STAFF_COMMAND_ROLE_ID = int(os.getenv("STAFF_COMMAND_ROLE_ID", "0"))


def can_use_say(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True

    return any(role.id == STAFF_COMMAND_ROLE_ID for role in member.roles)


class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="say", description="Send a message as the bot.")
    @app_commands.describe(message="The message the bot should send.")
    async def say(self, interaction: discord.Interaction, message: str):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("Use this in a server text channel.", ephemeral=True)
            return

        if not can_use_say(interaction.user):
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.channel.send(message)
        await interaction.delete_original_response()


async def setup(bot):
    await bot.add_cog(Say(bot))
