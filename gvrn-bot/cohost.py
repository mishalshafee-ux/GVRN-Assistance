import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

COLOR = 0xF5935F
DATA_FILE = Path("cohost_data.json")


def load_data():
    if not DATA_FILE.exists():
        return {}
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


class EndCohostView(discord.ui.View):
    def __init__(self, cog, user_id: int, guild_id: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id

    @discord.ui.button(label="End Co-Hosting", style=discord.ButtonStyle.danger)
    async def end_cohost(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return

        data = load_data()
        guild_key = str(self.guild_id)
        active = data.get(guild_key, [])

        if self.user_id in active:
            active.remove(self.user_id)
            data[guild_key] = active
            save_data(data)

        embed = discord.Embed(
            description=f"{interaction.user.mention} has ended co-hosting.",
            color=COLOR,
        )

        await interaction.response.edit_message(content="Co-hosting ended.", embed=None, view=None)
        await interaction.channel.send(embed=embed)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return

        await interaction.response.edit_message(content="Cancelled.", embed=None, view=None)


class Cohost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="cohost", description="Start or end co-hosting.")
    async def cohost(self, interaction: discord.Interaction):
        data = load_data()
        guild_key = str(interaction.guild.id)
        active = data.get(guild_key, [])

        if interaction.user.id in active:
            await interaction.response.send_message(
                "You are already co-hosting. Do you want to end co-hosting?",
                ephemeral=True,
                view=EndCohostView(self, interaction.user.id, interaction.guild.id),
            )
            return

        active.append(interaction.user.id)
        data[guild_key] = active
        save_data(data)

        embed = discord.Embed(
            description=(
                f"{interaction.user.mention} has started co-hosting.\n"
                "Please refer to this user when the host is busy."
            ),
            color=COLOR,
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Cohost(bot))
