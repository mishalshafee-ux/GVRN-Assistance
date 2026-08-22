import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0") or 0)

if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN in .env")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=["!", "?"], intents=intents)

EXTENSIONS = [
    "tickets",
    "vehicle_registration",
    "sessions",
    "early_access",
    "release_session",
    "regen",
    "reinvites",
    "over",
    "staff_adjustment",
    "welcome",
    "command_list",
    "partnership_requirements",
    "verification",
    "advertisements",
    "applications",
    "session_info",
    "infractions",
    "role_tools",
    "partners",
    "say",
    "server_stats",
    "suggestions",
]


async def update_presence():
    guild = bot.get_guild(GUILD_ID) if GUILD_ID else None
    member_count = guild.member_count if guild and guild.member_count else 0

    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"over {member_count} members",
        ),
    )


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    await update_presence()
    print("Presence set to DND watching member count.")

    try:
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild {GUILD_ID}")
        else:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} global commands")
    except Exception as error:
        print(f"Command sync failed: {error}")


async def main():
    async with bot:
        for extension in EXTENSIONS:
            try:
                await bot.load_extension(extension)
                print(f"Loaded extension: {extension}")
            except Exception as error:
                print(f"Failed to load {extension}: {error}")

        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
