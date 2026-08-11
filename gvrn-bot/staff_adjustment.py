import os

import discord
from discord import app_commands
from discord.ext import commands

STAFF_ADJUSTMENT_LOG_CHANNEL_ID = int(os.getenv("STAFF_ADJUSTMENT_LOG_CHANNEL_ID", "0"))
HIGH_COMMAND_ROLE_ID = int(os.getenv("HIGH_COMMAND_ROLE_ID", "0"))

ADJUSTMENT_EMOJI = "✦"


def is_high_command(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True

    return any(role.id == HIGH_COMMAND_ROLE_ID for role in member.roles)


class StaffAdjustment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="staff-adjustment", description="Send a staff adjustment message.")
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
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        if not is_high_command(interaction.user):
            await interaction.response.send_message(
                "You need High Command+ to use this command.",
                ephemeral=True,
            )
            return

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
        sent_message = await interaction.channel.send(message)

        log_channel = interaction.guild.get_channel(STAFF_ADJUSTMENT_LOG_CHANNEL_ID)
        if isinstance(log_channel, discord.TextChannel):
            log_embed = discord.Embed(title="Staff Adjustment Logged", color=0x76F55D)
            log_embed.add_field(name="Staff Member", value=staff_member.mention, inline=False)
            log_embed.add_field(name="Old Rank", value=old_rank, inline=True)
            log_embed.add_field(name="New Rank", value=new_rank, inline=True)
            log_embed.add_field(name="Reason", value=reason, inline=False)
            log_embed.add_field(name="Posted By", value=interaction.user.mention, inline=True)
            log_embed.add_field(name="Message", value=sent_message.jump_url, inline=False)
            await log_channel.send(embed=log_embed)

        await interaction.delete_original_response()


async def setup(bot):
    await bot.add_cog(StaffAdjustment(bot))
