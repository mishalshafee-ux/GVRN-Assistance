import os

import discord
from discord import app_commands
from discord.ext import commands

REINVITES_PING_ROLE_ID = int(os.getenv("REINVITES_PING_ROLE_ID", "0"))
REINVITES_IMAGE_URL = os.getenv("REINVITES_IMAGE_URL", "")

# =========================
# RE-INVITES EMBED EDIT AREA
# =========================


STAFF_COMMAND_ROLE_ID = int(os.getenv("STAFF_COMMAND_ROLE_ID", "0"))


def is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True

    return any(role.id == STAFF_COMMAND_ROLE_ID for role in member.roles)

SERVER_NAME = "GVRN"
REINVITES_COLOR = 0xE7F6FF
REINVITES_TITLE = "Greenville Community Roleplay - Roleplay Session Reinvites"

# =========================
# END RE-INVITES EMBED EDIT AREA
# =========================


class ReInvites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="re-invites",
        description="Send session reinvites.",
    )
    @app_commands.describe(
        frp_speed="Fail roleplay speed limit.",
        peacetime="Peacetime status.",
        leo_status="Law enforcement status.",
        session_link="Private server/session link.",
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
    async def re_invites(
        self,
        interaction: discord.Interaction,
        frp_speed: app_commands.Choice[str],
        peacetime: app_commands.Choice[str],
        leo_status: app_commands.Choice[str],
        session_link: str,
    ):
        if interaction.guild is None:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        if not is_staff(interaction.user):
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True,
            )
            return

        ping_role = interaction.guild.get_role(REINVITES_PING_ROLE_ID)

        content = ""
        if ping_role:
            content = ping_role.mention

        embed = discord.Embed(
            description=(
                f"❤ **{REINVITES_TITLE}** ❤\n\n"
                f"▬ {interaction.user.mention} has now released **reinvites** for their session! "
                f"You are welcome to join using the link found below. Before joining the session, "
                f"ensure you've read the information below regarding the session.\n\n"
                f"**Roleplay Information**\n\n"
                f"● **Peacetime Status:** `{peacetime.value}`.\n"
                f"● **Fail Roleplay Speeds:** `{frp_speed.value}`\n"
                f"● **Law Enforcement:** `{leo_status.value}`\n"
                f"↪ Pullover Speeds are **6+** the posted speed limit.\n\n"
                f"↪ Any member caught excessively fail roleplaying will result in being kicked from the session."
            ),
            color=REINVITES_COLOR,
        )

        if REINVITES_IMAGE_URL:
            embed.set_image(url=REINVITES_IMAGE_URL)

        embed.set_footer(text=f"{SERVER_NAME} Re-Invites")

        view = discord.ui.View(timeout=None)
        view.add_item(
            discord.ui.Button(
                label="Re-Invites Link",
                style=discord.ButtonStyle.link,
                url=session_link,
            )
        )

        await interaction.response.send_message(
            content=content,
            embed=embed,
            view=view,
            allowed_mentions=discord.AllowedMentions(roles=True, users=True),
        )


async def setup(bot):
    await bot.add_cog(ReInvites(bot))
