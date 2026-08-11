import os

import discord
from discord import app_commands
from discord.ext import commands

EA_PING_ROLE_ID = int(os.getenv("EA_PING_ROLE_ID", "0"))
EA_REQUIRED_ROLE_ID = int(os.getenv("EA_REQUIRED_ROLE_ID", "0"))
EA_IMAGE_URL = os.getenv("EA_IMAGE_URL", "")

# =========================
# EARLY ACCESS EDIT AREA
# =========================


STAFF_COMMAND_ROLE_ID = int(os.getenv("STAFF_COMMAND_ROLE_ID", "0"))


def is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True

    return any(role.id == STAFF_COMMAND_ROLE_ID for role in member.roles)

SERVER_NAME = "GVRN"
EA_COLOR = 0x76F55D

EA_TITLE = "Session Early Access"
EA_DESCRIPTION = (
    "▬ Early access has been **released for the session**. Nitro Contributors, "
    "Early Access, and Staff Team members may now join using the link below. "
    "Sharing this link will result in a permanent removal of your early access permissions.\n\n"
    "➜ Want to join **Early Access?** Become a **Nitro Contributor** or purchase "
    "**Early Access** from **marketplace**!"
)

EA_BUTTON_LABEL = "Early Access"

# =========================
# END EARLY ACCESS EDIT AREA
# =========================


class EarlyAccessView(discord.ui.View):
    def __init__(self, private_server_link):
        super().__init__(timeout=None)
        self.private_server_link = private_server_link

    @discord.ui.button(
        label=EA_BUTTON_LABEL,
        style=discord.ButtonStyle.secondary,
        custom_id="early_access_button",
    )
    async def early_access_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        has_required_role = any(role.id == EA_REQUIRED_ROLE_ID for role in interaction.user.roles)

        if not has_required_role:
            await interaction.response.send_message(
                "You do not have permission to use this Early Access button.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Early Access link: {self.private_server_link}",
            ephemeral=True,
        )


class EarlyAccess(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ea",
        description="Send the Early Access session message.",
    )
    @app_commands.describe(
        private_server_link="The private server link for Early Access users.",
    )
    async def ea(self, interaction: discord.Interaction, private_server_link: str):
        if interaction.guild is None:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        if not is_staff(interaction.user):
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True,
            )
            return

        ping_role = interaction.guild.get_role(EA_PING_ROLE_ID)

        content = ""
        if ping_role:
            content = ping_role.mention

        embed = discord.Embed(
            description=f"❤ **__{EA_TITLE}__** ❤\n\n{EA_DESCRIPTION}",
            color=EA_COLOR,
        )

        if EA_IMAGE_URL:
            embed.set_image(url=EA_IMAGE_URL)

        embed.set_footer(text=f"{SERVER_NAME} Early Access")

        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.channel.send(
            content=content,
            embed=embed,
            view=EarlyAccessView(private_server_link),
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        await interaction.delete_original_response()


async def setup(bot):
    await bot.add_cog(EarlyAccess(bot))
