import os
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from session_cleanup import clear_session_embeds
from session_state import save_session_start

COLOR = 0xEAC5FD

SESSION_PING_ROLE_ID = int(os.getenv("SESSION_PING_ROLE_ID", "0") or 0)
STAFF_COMMAND_ROLE_ID = int(os.getenv("STAFF_COMMAND_ROLE_ID", "0") or 0)
SESSION_STAFF_CHANNEL_ID = int(os.getenv("SESSION_STAFF_CHANNEL_ID", "0") or 0)
SESSION_IMAGE_URL = os.getenv("SESSION_IMAGE_URL", "")
SESSION_REACTION_EMOJI = os.getenv("SESSION_REACTION_EMOJI", "✅")

SESSION_VOTES = {}


def can_use_session_command(member: discord.Member):
    if member.guild_permissions.manage_guild:
        return True

    return any(role.id == STAFF_COMMAND_ROLE_ID for role in member.roles)


def role_mention(role_id):
    return f"<@&{role_id}>" if role_id else ""


class Session(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    session = app_commands.Group(name="session", description="Session commands.")

    @session.command(name="startup", description="Start a roleplay session vote.")
    @app_commands.describe(required_reactions="Required reactions before setup notice")
    async def startup(self, interaction: discord.Interaction, required_reactions: int = 10):
        await interaction.response.defer(ephemeral=True)

        if not can_use_session_command(interaction.user):
            await interaction.followup.send("You do not have permission to use this command.", ephemeral=True)
            return

        if required_reactions < 1:
            await interaction.followup.send("Required reactions must be at least 1.", ephemeral=True)
            return

        await clear_session_embeds(interaction.channel)

        ping = role_mention(SESSION_PING_ROLE_ID)

        embed = discord.Embed(
            title="Greenville Roleplay Network - Roleplay Session Startup",
            description=(
                f"› {interaction.user.mention} is hosting a roleplay session! If you intend on joining, "
                "react below with the host's chosen reaction. If you react without joining, you could face "
                "consequences from the staff team!\n\n"
                "**Before Joining**\n\n"
                "➜ Ensure you are verified **here**.\n"
                "➜ Read information before joining.\n"
                "➜ Register your vehicles in **/vehicle-registeration**.\n\n"
                f"↪ The host must get **{required_reactions}+** reactions before starting."
            ),
            color=COLOR,
        )
        embed.set_footer(text="GVRN Sessions")

        if SESSION_IMAGE_URL:
            embed.set_image(url=SESSION_IMAGE_URL)

        message = await interaction.channel.send(
            content=ping,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

        try:
            await message.add_reaction(SESSION_REACTION_EMOJI)
        except discord.HTTPException:
            pass

        SESSION_VOTES[message.id] = {
            "required": required_reactions,
            "host_id": interaction.user.id,
            "sent_setup": False,
            "channel_id": interaction.channel.id,
            "guild_id": interaction.guild.id,
        }

        save_session_start(interaction.guild.id)

        await interaction.followup.send("Session startup sent.", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        data = SESSION_VOTES.get(payload.message_id)

        if not data or data.get("sent_setup"):
            return

        if payload.user_id == self.bot.user.id:
            return

        channel = self.bot.get_channel(data["channel_id"])
        if not isinstance(channel, discord.TextChannel):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.HTTPException:
            return

        reaction_count = 0

        for reaction in message.reactions:
            if str(reaction.emoji) == SESSION_REACTION_EMOJI:
                reaction_count = reaction.count
                break

        if reaction_count < data["required"]:
            return

        data["sent_setup"] = True

        setup_embed = discord.Embed(
            title="Session Setup",
            description=(
                "The required votes have been reached. Please wait **5-10 minutes** while the host "
                "sets up the session."
            ),
            color=COLOR,
        )
        setup_embed.set_footer(text="GVRN Sessions")

        await channel.send(embed=setup_embed)

        staff_channel = self.bot.get_channel(SESSION_STAFF_CHANNEL_ID)
        if isinstance(staff_channel, discord.TextChannel):
            await staff_channel.send(
                f"<@{data['host_id']}> your session vote reached **{data['required']}** reactions.",
                allowed_mentions=discord.AllowedMentions(users=True),
            )


async def setup(bot):
    await bot.add_cog(Session(bot))
