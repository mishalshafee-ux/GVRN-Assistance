import os
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from session_cleanup import clear_session_embeds

COLOR = 0xD3E6FF

OVER_IMAGE_URL = os.getenv("OVER_IMAGE_URL", "")
SESSION_PING_ROLE_ID = int(os.getenv("SESSION_PING_ROLE_ID", "0") or 0)
STAFF_COMMAND_ROLE_ID = int(os.getenv("STAFF_COMMAND_ROLE_ID", "0") or 0)

SESSION_START_TIMES = {}


def can_use_session_command(member: discord.Member):
    if member.guild_permissions.manage_guild:
        return True

    return any(role.id == STAFF_COMMAND_ROLE_ID for role in member.roles)


def duration_text(started_at):
    if not started_at:
        return "Unknown"

    seconds = int((datetime.now(timezone.utc) - started_at).total_seconds())
    minutes = max(seconds // 60, 0)

    if minutes < 1:
        return "Less than 1 Minute"

    if minutes == 1:
        return "1 Minute"

    return f"{minutes} Minutes"


class SessionOver(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="over", description="Conclude the current session.")
    async def over(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not can_use_session_command(interaction.user):
            await interaction.followup.send("You do not have permission to use this command.", ephemeral=True)
            return

        deleted = await clear_session_embeds(interaction.channel)

        started_at = SESSION_START_TIMES.get(interaction.guild.id)
        duration = duration_text(started_at)

        embed = discord.Embed(
            title="Greenville Roleplay Network - Session Conclusion",
            description=(
                f"› {interaction.user.mention} has unfortunately concluded their session. "
                "We thank you all for those who attended, and hope to see you in future sessions. "
                "Please do **not** ask any staff to host as it may result in punishment.\n\n"
                f"**Session Duration** {duration}"
            ),
            color=COLOR,
        )
        embed.set_footer(text="GVRN Session Concluded")

        if OVER_IMAGE_URL:
            embed.set_image(url=OVER_IMAGE_URL)

        await interaction.channel.send(embed=embed)
        await interaction.followup.send(f"Session concluded. Removed {deleted} old session message(s).", ephemeral=True)


async def setup(bot):
    await bot.add_cog(SessionOver(bot))
