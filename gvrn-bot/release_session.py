import os

import discord
from discord import app_commands
from discord.ext import commands

COLOR = 0xD3E6FF
RELEASE_PING_ROLE_ID = int(os.getenv("RELEASE_PING_ROLE_ID", "0") or 0)
RELEASE_IMAGE_URL = os.getenv("RELEASE_IMAGE_URL", "")
RELEASE_VIDEO_URL = os.getenv("RELEASE_VIDEO_URL", "")
STAFF_COMMAND_ROLE_ID = int(os.getenv("STAFF_COMMAND_ROLE_ID", "0") or 0)


def can_use(member: discord.Member) -> bool:
    return member.guild_permissions.administrator or any(role.id == STAFF_COMMAND_ROLE_ID for role in member.roles)


class ServerCodeView(discord.ui.View):
    def __init__(self, code: str):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label=f"Server Code: {code}", style=discord.ButtonStyle.secondary, disabled=True))


class ReleaseSession(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="release", description="Release the roleplay session code.")
    @app_commands.describe(
        session_code="The Greenville server code, like AAAKF",
        message="Extra message to show on the release embed.",
    )
    async def release(self, interaction: discord.Interaction, session_code: str, message: str = "Join up and enjoy the session."):
        if not can_use(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        ping = f"<@&{RELEASE_PING_ROLE_ID}>" if RELEASE_PING_ROLE_ID else ""

        embed = discord.Embed(
            title="Greenville Roleplay Network — Session Released",
            description=(
                f"{message}\n\n"
                f"**Server Code:** `{session_code}`"
            ),
            color=COLOR,
        )

        if RELEASE_IMAGE_URL:
            embed.set_image(url=RELEASE_IMAGE_URL)

        embed.set_footer(text="GVRN Sessions")

        await interaction.channel.send(content=ping, embed=embed, view=ServerCodeView(session_code))

        if RELEASE_VIDEO_URL:
            await interaction.channel.send(RELEASE_VIDEO_URL)

        await interaction.followup.send("Session release sent.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ReleaseSession(bot))
