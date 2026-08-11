import discord
from discord import app_commands
from discord.ext import commands

# =========================
# STAFF ADJUSTMENT EDIT AREA
# =========================

ADJUSTMENT_EMOJI = "✦"

# =========================
# END STAFF ADJUSTMENT EDIT AREA
# =========================


class StaffAdjustment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="staff-adjustment",
        description="Send a staff adjustment message.",
    )
    @app_commands.describe(
        adjustment_number="Example: 2",
        staff_member="The staff member being adjusted.",
        old_rank="Example: Executive Owner",
        new_rank="Example: Ownership Helper",
        reason="Reason for the adjustment.",
        footer_name="Example: Marcus / Executive Owner",
    )
    async def staff_adjustment(
        self,
        interaction: discord.Interaction,
        adjustment_number: int,
        staff_member: discord.Member,
        old_rank: str,
        new_rank: str,
        reason: str,
        footer_name: str,
    ):
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("Use this in a server text channel.", ephemeral=True)
            return

        message = (
            f"# {ADJUSTMENT_EMOJI} Staff Adjustment {adjustment_number}\n"
            f"• {staff_member.mention}\n"
            f"• {old_rank} ➜ {new_rank}\n"
            f"• Reason: {reason}\n\n"
            f"*{footer_name}*"
        )

        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.channel.send(message)
        await interaction.delete_original_response()


async def setup(bot):
    await bot.add_cog(StaffAdjustment(bot))
