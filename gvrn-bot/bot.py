import asyncio
import os

import discord
from discord.ext import commands, tasks
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


async def update_presence():
    member_count = 0

    for guild in bot.guilds:
        member_count += guild.member_count or 0

    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"over {member_count} members",
        ),
    )


@tasks.loop(minutes=10)
async def presence_loop():
    await update_presence()


@bot.event
async def on_ready():
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to guild {GUILD_ID}")
    else:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global commands")

    await update_presence()

    if not presence_loop.is_running():
        presence_loop.start()

    print(f"Logged in as {bot.user}")


@bot.event
async def on_member_join(member):
    await update_presence()


@bot.event
async def on_member_remove(member):
    await update_presence()


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
        await bot.load_extension("modlog")
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
