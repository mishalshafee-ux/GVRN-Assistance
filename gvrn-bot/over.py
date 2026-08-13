import json
import os
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from session_cleanup import clear_session_embeds

OVER_IMAGE_URL = os.getenv("OVER_IMAGE_URL", "")
SESSION_STATE_FILE = Path("session_state.json")


STAFF_COMMAND_ROLE_ID = int(os.getenv("STAFF_COMMAND_ROLE_ID", "0"))


def is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True

    return any(role.id == STAFF_COMMAND_ROLE_ID for role in member.roles)

SERVER_NAME = "GVRN"
OVER_COLOR = 0x76F55D
OVER_TITLE = "Greenville Community Roleplay - Session Conclusion"


def get_session_duration_text():
    if not SESSION_STATE_FILE.exists():
        return "Unknown"

    with SESSION_STATE_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    started_at = datetime.fromisoformat(data["started_at"])
    now = datetime.now(timezone.utc)
    minutes = max(int((now - started_at).total_seconds()) // 60, 1)

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours and remaining_minutes:
        return f"{hours} Hour(s) {remaining_minutes} Minute(s)"
    if hours:
        return f"{hours} Hour(s)"
    return f"{minutes} Minute(s)"


def build_over_embed(user):
    embed = discord.Embed(
        description=(
            f"·❤· **{OVER_TITLE}** ·❤·\n\n"
            f"》 {user.mention} has unfortunately concluded their session! "
            f"We thank you all for those who attended, and hope to see you in future sessions. "
            f"Please do **not** ask any staff to host as it may result in punishment.\n\n"
            f"**Session Duration** {get_session_duration_text()}"
        ),
        color=OVER_COLOR,
    )

    if OVER_IMAGE_URL:
        embed.set_image(url=OVER_IMAGE_URL)

    embed.set_footer(text=f"{SERVER_NAME} Session Concluded")
    return embed


class SessionOver(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def clear_session_messages(self, channel):
        await clear_session_embeds(channel, self.bot.user)

    async def post_over(self, channel, user):
        await self.clear_session_messages(channel)
        await channel.send(embed=build_over_embed(user))

        if SESSION_STATE_FILE.exists():
            SESSION_STATE_FILE.unlink()

    @app_commands.command(name="over", description="Conclude the current roleplay session.")
    async def over_slash(self, interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("Use this in a server text channel.", ephemeral=True)
            return

        if not is_staff(interaction.user):
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=False)

        try:
            await self.post_over(interaction.channel, interaction.user)
        except discord.Forbidden:
            await interaction.followup.send(
                "I need Manage Messages permission to delete old session messages.",
                ephemeral=True,
            )
            return

        await interaction.delete_original_response()


async def setup(bot):
    await bot.add_cog(SessionOver(bot))
