import os

import discord
from discord.ext import commands

VERIFY_ROLE_ID = int(os.getenv("VERIFY_ROLE_ID", "0"))
UNVERIFIED_ROLE_ID = int(os.getenv("UNVERIFIED_ROLE_ID", "0"))

SERVER_NAME = "GVRN"
VERIFY_COLOR = 0x76F55D
VERIFY_TITLE = "GVRN Verification"
VERIFY_DESCRIPTION = (
    "Welcome to **GVRN**.\n\n"
    "Click the button below to verify yourself and gain access to the server."
)
VERIFY_BUTTON_LABEL = "Verify"


class RobloxUsernameModal(discord.ui.Modal, title="GVRN Verification"):
    roblox_username = discord.ui.TextInput(
        label="Roblox Username",
        placeholder="Example: Mishal734567",
        max_length=32,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        verified_role = interaction.guild.get_role(VERIFY_ROLE_ID)
        unverified_role = interaction.guild.get_role(UNVERIFIED_ROLE_ID)

        if verified_role is None:
            await interaction.response.send_message("Verify role was not found.", ephemeral=True)
            return

        roblox_username = str(self.roblox_username.value).strip().replace("@", "")
        new_nickname = f"{interaction.user.display_name} (@{roblox_username})"

        try:
            await interaction.user.add_roles(verified_role, reason="User verified with button.")
            if unverified_role and unverified_role in interaction.user.roles:
                await interaction.user.remove_roles(unverified_role, reason="User verified with button.")

            await interaction.user.edit(nick=new_nickname[:32], reason="User verified with Roblox username.")
        except discord.Forbidden:
            await interaction.response.send_message(
                "I cannot update your roles or nickname. Check my role position and permissions.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"You have been verified as `{new_nickname[:32]}`.",
            ephemeral=True,
        )


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label=VERIFY_BUTTON_LABEL,
        style=discord.ButtonStyle.success,
        custom_id="verify_button",
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        await interaction.response.send_modal(RobloxUsernameModal())


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(VerifyView())

    @commands.command(name="verifypanel")
    @commands.has_permissions(administrator=True)
    async def verifypanel(self, ctx):
        embed = discord.Embed(
            title=VERIFY_TITLE,
            description=VERIFY_DESCRIPTION,
            color=VERIFY_COLOR,
        )
        embed.set_footer(text=f"{SERVER_NAME} Verification")

        await ctx.send(embed=embed, view=VerifyView())

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass


async def setup(bot):
    await bot.add_cog(Verification(bot))
