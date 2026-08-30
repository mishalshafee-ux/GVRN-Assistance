import os

import discord
from discord import app_commands
from discord.ext import commands

COLOR = 0xD3E6FF

RELEASE_PING_ROLE_ID = int(os.getenv("RELEASE_PING_ROLE_ID", "0") or 0)
RELEASE_IMAGE_URL = os.getenv("RELEASE_IMAGE_URL", "")
RELEASE_VIDEO_URL = os.getenv("RELEASE_VIDEO_URL", "")
STAFF_COMMAND_ROLE_ID = int(os.getenv("STAFF_COMMAND_ROLE_ID", "0") or 0)


def can_use_session_command(member: discord.Member):
    if member.guild_permissions.manage_guild:
        return True

    return any(role.id == STAFF_COMMAND_ROLE_ID for role in member.roles)


class ServerCodeView(discord.ui.View):
    def __init__(self, session_code: str):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label=f"Server Code: {session_code}",
                style=discord.ButtonStyle.secondary,
                disabled=True,
            )
        )


class ReleaseSession(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="release", description="Release the current roleplay session.")
    @app_commands.describe(
        frp_speed="Fail roleplay speed",
        peacetime="Peacetime status",
        leo_status="Law enforcement status",
        session_code="Private server code, example AAAKF",
    )
    @app_commands.choices(
        frp_speed=[
            app_commands.Choice(name="65", value="65"),
            app_commands.Choice(name="75", value="75"),
            app_commands.Choice(name="100", value="100"),
        ],
        peacetime=[
            app_commands.Choice(name="Strict", value="Strict Peacetime"),
            app_commands.Choice(name="On", value="On"),
            app_commands.Choice(name="Off", value="Off"),
        ],
        leo_status=[
            app_commands.Choice(name="Online", value="Online"),
            app_commands.Choice(name="Offline", value="Offline"),
        ],
    )
    async def release(
        self,
        interaction: discord.Interaction,
        frp_speed: app_commands.Choice[str],
        peacetime: app_commands.Choice[str],
        leo_status: app_commands.Choice[str],
        session_code: str,
    ):
        await interaction.response.defer(ephemeral=True)

        if not can_use_session_command(interaction.user):
            if RELEASE_VIDEO_URL:
            await interaction.channel.send(RELEASE_VIDEO_URL)

        await interaction.followup.send("You do not have permission to use this command.", ephemeral=True)
            return

        ping = f"<@&{RELEASE_PING_ROLE_ID}>" if RELEASE_PING_ROLE_ID else ""

        embed = discord.Embed(
            title="Greenville Roleplay Network - Roleplay Session Released",
            description=(
                f"— {interaction.user.mention} has now released their session! You are welcome to join "
                "using the server code found below. Before joining the session, ensure you have read the "
                "information below regarding the session.\n\n"
                "**Roleplay Information**\n\n"
                f"• **Peacetime Status:** `{peacetime.value}`.\n"
                f"• **Fail Roleplay Speeds:** `{frp_speed.value}`\n"
                f"• **Law Enforcement:** `{leo_status.value}`\n"
                "↪ Pullover Speeds are **6+** the posted speed limit.\n\n"
                "➜ Any member caught excessively fail roleplaying will result in being kicked from the session."
            ),
            color=COLOR,
        )
        embed.set_footer(text="GVRN Session Released")

        if RELEASE_IMAGE_URL:
            embed.set_image(url=RELEASE_IMAGE_URL)

        await interaction.channel.send(
            content=ping,
            embed=embed,
            view=ServerCodeView(session_code),
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

        await interaction.followup.send("Session released.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ReleaseSession(bot))
