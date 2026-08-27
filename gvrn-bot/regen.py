import os

import discord
from discord import app_commands
from discord.ext import commands

REGEN_PING_ROLE_ID = int(os.getenv("REGEN_PING_ROLE_ID", "0"))

# =========================
# REGEN EMBED EDIT AREA
# =========================


STAFF_COMMAND_ROLE_ID = int(os.getenv("STAFF_COMMAND_ROLE_ID", "0"))


def is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True

    return any(role.id == STAFF_COMMAND_ROLE_ID for role in member.roles)

SERVER_NAME = "Greenville Community Roleplay"
REGEN_COLOR = 0xD3E6FF
REGEN_TITLE = "Link Regeneration"

REGEN_DESCRIPTION = (
    "› The host has now **regenerated** the current session link. "
    "Please wait **patiently for reinvites**, they will occur once the session "
    "has spots opened for more users."
)

REGEN_THUMBNAIL_URL = ""

# =========================
# END REGEN EMBED EDIT AREA
# =========================


class Regen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="regen",
        description="Send the link regeneration message.",
    )
    async def regen(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        if not is_staff(interaction.user):
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True,
            )
            return

        ping_role = interaction.guild.get_role(REGEN_PING_ROLE_ID)

        content = ""
        if ping_role:
            content = ping_role.mention

        embed = discord.Embed(
            description=(
                f"·❤· **__{REGEN_TITLE}__** ·❤·\n\n"
                f"{REGEN_DESCRIPTION}\n\n"
                f"**{SERVER_NAME}**"
            ),
            color=REGEN_COLOR,
        )

        if REGEN_THUMBNAIL_URL:
            embed.set_thumbnail(url=REGEN_THUMBNAIL_URL)

        await interaction.response.send_message(
            content=content,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )


async def setup(bot):
    await bot.add_cog(Regen(bot))
