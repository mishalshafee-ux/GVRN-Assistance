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

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="GVRN Assistance",
        ),
    )

    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to guild {GUILD_ID}")
    else:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global commands")

    print(f"Logged in as {bot.user}")


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
        await bot.load_extension("verification")
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
