import asyncio
import os
from pathlib import Path
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
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
    "ai_tickets",
    "ai_control",
    "ticket_ai_control",
    "status_roles",
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
    "moderation_tools",
    "cohost",
    "check_perms",
    "roblox_verification",
    "extra_commands",
]



@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: discord.app_commands.AppCommandError,
):
    original = getattr(error, "original", error)

    print("[SLASH COMMAND ERROR]")
    traceback.print_exception(type(original), original, original.__traceback__)

    message = f"Command error: {type(original).__name__}: {original}"

    try:
        if interaction.response.is_done():
            await interaction.followup.send(message[:1900], ephemeral=True)
        else:
            await interaction.response.send_message(message[:1900], ephemeral=True)
    except Exception as response_error:
        print(f"Could not send error response: {response_error}")

async def update_presence():
    guild = bot.get_guild(GUILD_ID) if GUILD_ID else None

    if guild is None and GUILD_ID:
        try:
            guild = await bot.fetch_guild(GUILD_ID)
        except discord.HTTPException as error:
            print(f"Could not fetch configured guild {GUILD_ID}: {error}")

    member_count = guild.member_count if guild and guild.member_count else 0

    print(f"Configured GUILD_ID: {GUILD_ID}")
    print(f"Connected guilds: {[(item.name, item.id) for item in bot.guilds]}")
    print(f"Target guild found: {guild is not None}")
    print(f"Member count: {member_count}")

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
