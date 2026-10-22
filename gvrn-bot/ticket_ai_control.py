import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

SETTINGS_FILE = Path(__file__).with_name("ticket_ai_settings.json")


def load_settings():
    try:
        return json.loads(SETTINGS_FILE.read_text())
    except Exception:
        return {}


def save_settings(settings):
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2))


def is_ticket_ai_enabled(channel_id):
    return load_settings().get(str(channel_id), False)


def is_ticket_channel(channel):
    topic = (getattr(channel, "topic", "") or "").lower()
    name = (getattr(channel, "name", "") or "").lower()
    category = (getattr(getattr(channel, "category", None), "name", "") or "").lower()

    return (
        topic.startswith("ticket-owner:")
        or "ticket" in name
        or "ticket" in category
    )


class TicketAIControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ticket-ai",
        description="Enable or disable AI replies in this ticket",
    )
    @app_commands.describe(mode="Turn ticket AI on or off")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="On", value="on"),
            app_commands.Choice(name="Off", value="off"),
        ]
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_ai(
        self,
        interaction: discord.Interaction,
        mode: app_commands.Choice[str],
    ):
        if not interaction.channel or not is_ticket_channel(interaction.channel):
            await interaction.response.send_message(
                "This command can only be used inside a ticket.",
                ephemeral=True,
            )
            return

        settings = load_settings()
        enabled = mode.value == "on"
        settings[str(interaction.channel.id)] = enabled
        save_settings(settings)

        status = "enabled" if enabled else "disabled"

        await interaction.response.send_message(
            f"AI replies are now **{status}** in this ticket.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(TicketAIControl(bot))
