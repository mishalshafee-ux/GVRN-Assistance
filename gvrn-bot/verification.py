import os

import discord
from discord.ext import commands

VERIFY_ROLE_ID = int(os.getenv("VERIFY_ROLE_ID", "0"))

SERVER_NAME = "GVRN"
VERIFY_COLOR = 0x76F55D
VERIFY_TITLE = "GVRN Verification"
VERIFY_DESCRIPTION = (
    "Welcome to **GVRN**.\n\n"
    "Click the button below to verify yourself and gain access to the server."
)
VERIFY_BUTTON_LABEL = "Verify"


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

        role = interaction.guild.get_role(VERIFY_ROLE_ID)

        if role is None:
            await interaction.response.send_message("Verify role was not found.", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.response.send_message("You are already verified.", ephemeral=True)
            return

        try:
            await interaction.user.add_roles(role, reason="User verified with button.")
        except discord.Forbidden:
            await interaction.response.send_message(
                "I cannot give that role. Move my bot role above the verify role.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"You have been verified and received {role.mention}.",
            ephemeral=True,
        )


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
