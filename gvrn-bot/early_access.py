import os

import discord
from discord import app_commands
from discord.ext import commands

COLOR = 0xD3E6FF
EA_PING_ROLE_ID = int(os.getenv("EA_PING_ROLE_ID", "0") or 0)
EA_REQUIRED_ROLE_ID = int(os.getenv("EA_REQUIRED_ROLE_ID", "0") or 0)
EA_IMAGE_URL = os.getenv("EA_IMAGE_URL", "")
STAFF_COMMAND_ROLE_ID = int(os.getenv("STAFF_COMMAND_ROLE_ID", "0") or 0)


def can_use(member: discord.Member) -> bool:
    return member.guild_permissions.administrator or any(role.id == STAFF_COMMAND_ROLE_ID for role in member.roles)


class EarlyAccessCodeView(discord.ui.View):
    def __init__(self, code: str):
        super().__init__(timeout=None)
        self.code = code

    @discord.ui.button(label="Get Server Code", style=discord.ButtonStyle.success)
    async def get_code(self, interaction: discord.Interaction, button: discord.ui.Button):
        if EA_REQUIRED_ROLE_ID:
            role = interaction.guild.get_role(EA_REQUIRED_ROLE_ID)
            if role not in interaction.user.roles:
                await interaction.response.send_message(
                    "You do not have Early Access.",
                    ephemeral=True,
                )
                return

        await interaction.response.send_message(
            f"Your Early Access server code is: `{self.code}`",
            ephemeral=True,
        )


class EarlyAccess(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ea", description="Send the early access session panel.")
    @app_commands.describe(
        code="The Greenville server code, like AAAKF",
        message="Extra message to show on the early access embed.",
    )
    async def ea(self, interaction: discord.Interaction, code: str, message: str = "Early access is now open."):
        if not can_use(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        ping = f"<@&{EA_PING_ROLE_ID}>" if EA_PING_ROLE_ID else ""

        embed = discord.Embed(
            title="Greenville Roleplay Network — Early Access",
            description=(
                f"{message}\n\n"
                "Press the button below to get the server code.\n"
                "Only Early Access members can see the code."
            ),
            color=COLOR,
        )

        if EA_REQUIRED_ROLE_ID:
            embed.add_field(
                name="Access",
                value=f"Only <@&{EA_REQUIRED_ROLE_ID}> may join during early access.",
                inline=False,
            )

        if EA_IMAGE_URL:
            embed.set_image(url=EA_IMAGE_URL)

        embed.set_footer(text="GVRN Sessions")

        await interaction.channel.send(content=ping, embed=embed, view=EarlyAccessCodeView(code))
        await interaction.followup.send("Early access panel sent.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(EarlyAccess(bot))
