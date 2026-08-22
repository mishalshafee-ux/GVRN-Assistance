import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN in .env")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=["!", "?"], intents=intents)


async def main():
    async with bot:
        await bot.load_extension("tickets")
        await bot.load_extension("vehicle_registration")
        await bot.load_extension("sessions")
        await bot.load_extension("early_access")
        await bot.load_extension("release_session")
        await bot.load_extension("regen")
        await bot.load_extension("reinvites")
        await bot.load_extension("over")
        await bot.load_extension("staff_adjustment")
        await bot.load_extension("welcome")
        await bot.load_extension("command_list")
        await bot.load_extension("partnership_requirements")
        await bot.load_extension("verification")
        await bot.load_extension("advertisements")
        await bot.load_extension("applications")
        await bot.load_extension("session_info")
        await bot.load_extension("infractions")
        await bot.load_extension("role_tools")
        await bot.load_extension("partners")
        await bot.load_extension("say")
        await bot.load_extension("server_stats")
        await bot.load_extension("suggestions")
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
