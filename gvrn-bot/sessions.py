import json
import os
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

SESSION_PING_ROLE_ID = int(os.getenv("SESSION_PING_ROLE_ID", "0"))
SESSION_REACTION_EMOJI = os.getenv("SESSION_REACTION_EMOJI", "🤍")
SESSION_IMAGE_URL = os.getenv("SESSION_IMAGE_URL", "")
SESSION_STAFF_CHANNEL_ID = int(os.getenv("SESSION_STAFF_CHANNEL_ID", "0"))
STAFF_COMMAND_ROLE_ID = int(os.getenv("STAFF_COMMAND_ROLE_ID", "0"))

SESSION_STATE_FILE = Path("session_state.json")

SERVER_NAME = "GVRN"
SESSION_TITLE = "Greenville Community Roleplay - Roleplay Session Startup"
SESSION_COLOR = 0xE7F6FF

BEFORE_JOINING_TEXT = (
    "➜ Ensure you are verified **here**.\n"
    "➜ Read **information** & the **banned vehicle list**.\n"
    "➜ Register your vehicles in **/vehicle-registeration**!"
)

SETUP_TITLE = "Session Setup"
SETUP_DESCRIPTION = (
    "The required votes have been reached. Please wait **5-10 minutes** "
    "while the host sets up the session."
)


def is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(role.id == STAFF_COMMAND_ROLE_ID for role in member.roles)


async def clear_session_embeds(channel: discord.TextChannel, bot_user: discord.ClientUser):
    def should_delete(message: discord.Message):
        return message.author.id == bot_user.id and bool(message.embeds)

    await channel.purge(
        limit=100,
        check=should_delete,
        bulk=True,
        reason="Clearing old session bot embeds before startup.",
    )


def save_session_start(host_id, message_id, required_reactions):
    data = {
        "host_id": host_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "startup_message_id": message_id,
        "required_reactions": required_reactions,
        "setup_sent": False,
    }

    with SESSION_STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def load_session_state():
    if not SESSION_STATE_FILE.exists():
        return None

    with SESSION_STATE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def update_session_state(data):
    with SESSION_STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def reaction_matches(reaction):
    configured = discord.PartialEmoji.from_str(SESSION_REACTION_EMOJI)

    if configured.id:
        return getattr(reaction.emoji, "id", None) == configured.id

    return str(reaction.emoji) == SESSION_REACTION_EMOJI


class Sessions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    session = app_commands.Group(name="session", description="Session commands.")

    @session.command(name="startup", description="Start a roleplay session vote.")
    @app_commands.describe(required_reactions="How many reactions are needed before starting")
    async def startup(self, interaction: discord.Interaction, required_reactions: int = 10):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("Use this in a server text channel.", ephemeral=True)
            return

        if not is_staff(interaction.user):
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=False)

        try:
            await clear_session_embeds(interaction.channel, self.bot.user)
        except discord.Forbidden:
            await interaction.followup.send(
                "I need Manage Messages permission to clear old session messages.",
                ephemeral=True,
            )
            return

        ping_role = interaction.guild.get_role(SESSION_PING_ROLE_ID)
        ping_text = ping_role.mention if ping_role else ""

        embed = discord.Embed(
            description=(
                f"♡ **{SESSION_TITLE}** ♡\n\n"
                f"》 {interaction.user.mention} is hosting a roleplay session! "
                f"If you intend on joining, react below with the host's chosen reaction. "
                f"If you react without joining, you could face consequences from the staff team!\n\n"
                f"**Before Joining**\n\n"
                f"{BEFORE_JOINING_TEXT}\n\n"
                f"↪ The host must get **{required_reactions}+** reactions before starting."
            ),
            color=SESSION_COLOR,
        )

        if SESSION_IMAGE_URL:
            embed.set_image(url=SESSION_IMAGE_URL)

        embed.set_footer(text=f"{SERVER_NAME} Sessions")

        message = await interaction.channel.send(
            content=ping_text,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True, users=True),
        )

        save_session_start(interaction.user.id, message.id, required_reactions)

        try:
            emoji = discord.PartialEmoji.from_str(SESSION_REACTION_EMOJI)
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await message.add_reaction("🤍")

        await interaction.delete_original_response()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        data = load_session_state()
        if not data or data.get("setup_sent"):
            return

        if reaction.message.id != data.get("startup_message_id"):
            return

        if not reaction_matches(reaction):
            return

        if reaction.count < int(data.get("required_reactions", 10)):
            return

        data["setup_sent"] = True
        update_session_state(data)

        setup_embed = discord.Embed(
            title=SETUP_TITLE,
            description=SETUP_DESCRIPTION,
            color=SESSION_COLOR,
        )
        setup_embed.set_footer(text=f"{SERVER_NAME} Sessions")

        await reaction.message.channel.send(embed=setup_embed)

        staff_channel = reaction.message.guild.get_channel(SESSION_STAFF_CHANNEL_ID)
        if isinstance(staff_channel, discord.TextChannel):
            await staff_channel.send(
                f"<@{data['host_id']}> your session has reached "
                f"**{data['required_reactions']}** reactions. Please begin setting up. "
                f"Members have been told to wait **5-10 minutes**."
            )


async def setup(bot):
    await bot.add_cog(Sessions(bot))
