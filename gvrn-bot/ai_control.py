import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

AI_SETTINGS_FILE = Path(__file__).with_name("ai_settings.json")


def load_settings():
    try:
        return json.loads(AI_SETTINGS_FILE.read_text())
    except Exception:
        return {}


def save_settings(settings):
    AI_SETTINGS_FILE.write_text(json.dumps(settings, indent=2))


def is_ai_enabled(guild_id):
    return load_settings().get(str(guild_id), True)


class AIControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ai", description="Turn the AI ticket assistant on or off")
    @app_commands.describe(mode="Choose whether the AI should be enabled")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="On", value="on"),
            app_commands.Choice(name="Off", value="off"),
        ]
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ai(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        settings = load_settings()
        settings[str(interaction.guild_id)] = mode.value == "on"
        save_settings(settings)

        status = "enabled" if mode.value == "on" else "disabled"

        await interaction.response.send_message(
            f"AI ticket replies are now **{status}**.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(AIControl(bot))
