import os

import discord
from discord import app_commands
from discord.ext import commands

RELEASE_PING_ROLE_ID = int(os.getenv("RELEASE_PING_ROLE_ID", "0"))
RELEASE_IMAGE_URL = os.getenv("RELEASE_IMAGE_URL", "")
STAFF_COMMAND_ROLE_ID = int(os.getenv("STAFF_COMMAND_ROLE_ID", "0"))

SERVER_NAME = "GVRN"
RELEASE_COLOR = 0xE7F6FF
RELEASE_TITLE = "Greenville Community Roleplay - Roleplay Session Released"


def is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(role.id == STAFF_COMMAND_ROLE_ID for role in member.roles)


class ReleaseSession(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="release", description="Release a roleplay session.")
    @app_commands.describe(
        frp_speed="Fail roleplay speed limit.",
        peacetime="Peacetime status.",
        leo_status="Law enforcement status.",
        session_link="Private server/session link. Must start with https://",
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
        session_link: str,
    ):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("Use this in a server text channel.", ephemeral=True)
            return

        if not is_staff(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        if not session_link.startswith(("https://", "http://")):
            await interaction.response.send_message("Session link must start with `https://`.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=False)

        try:
            ping_role = interaction.guild.get_role(RELEASE_PING_ROLE_ID)
            content = ping_role.mention if ping_role else ""

            embed = discord.Embed(
                description=(
                    f"☁ **{RELEASE_TITLE}** ☁\n\n"
                    f"▬ {interaction.user.mention} has now released their session! "
                    f"You are welcome to join using the link found below. Before joining the session, "
                    f"ensure you've read the information below regarding the session.\n\n"
                    f"**Roleplay Information**\n\n"
                    f"● **Peacetime Status:** `{peacetime.value}`.\n"
                    f"● **Fail Roleplay Speeds:** `{frp_speed.value}`\n"
                    f"● **Law Enforcement:** `{leo_status.value}`\n"
                    f"↪ Pullover Speeds are **6+** the posted speed limit.\n\n"
                    f"➜ Any member caught excessively fail roleplaying will result in being kicked from the session."
                ),
                color=RELEASE_COLOR,
            )

            if RELEASE_IMAGE_URL:
                embed.set_image(url=RELEASE_IMAGE_URL)

            embed.set_footer(text=f"{SERVER_NAME} Session Released")

            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Session Link", style=discord.ButtonStyle.link, url=session_link))

            await interaction.channel.send(
                content=content,
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions(roles=True, users=True),
            )
            await interaction.delete_original_response()

        except Exception as error:
            await interaction.followup.send(f"Release command error: `{error}`", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ReleaseSession(bot))
