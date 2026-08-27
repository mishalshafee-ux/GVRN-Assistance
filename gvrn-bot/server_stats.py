import os

import discord
from discord.ext import commands, tasks

GUILD_ID = int(os.getenv("GUILD_ID", "0"))
SERVER_STATS_MEMBERS_CHANNEL_ID = int(os.getenv("SERVER_STATS_MEMBERS_CHANNEL_ID", "0"))
SERVER_STATS_BOTS_CHANNEL_ID = int(os.getenv("SERVER_STATS_BOTS_CHANNEL_ID", "0"))


class ServerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    async def update_everything(self):
        guild = self.bot.get_guild(GUILD_ID) if GUILD_ID else None
        if not guild:
            print("Server stats: guild not found. Check GUILD_ID.")
            return

        try:
            await guild.chunk(cache=True)
        except Exception:
            pass

        bots = sum(1 for member in guild.members if member.bot)
        humans = sum(1 for member in guild.members if not member.bot)

        await self.bot.change_presence(
            status=discord.Status.dnd,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"over {humans} members",
            ),
        )

        member_channel = guild.get_channel(SERVER_STATS_MEMBERS_CHANNEL_ID)
        bot_channel = guild.get_channel(SERVER_STATS_BOTS_CHANNEL_ID)

        if member_channel:
            await self.rename_channel(member_channel, f"Members: {humans}")

        if bot_channel:
            await self.rename_channel(bot_channel, f"Bots: {bots}")

        print(f"Server stats updated: Members={humans}, Bots={bots}")

    @tasks.loop(minutes=1)
    async def update_stats(self):
        await self.update_everything()

    async def rename_channel(self, channel, name):
        if channel.name == name:
            return

        try:
            await channel.edit(name=name, reason="Updating server stats.")
        except discord.Forbidden:
            print(f"Missing Manage Channels permission for {channel.name}.")
        except discord.HTTPException as error:
            print(f"Could not rename {channel.name}: {error}")

    @update_stats.before_loop
    async def before_update_stats(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    cog = ServerStats(bot)
    await bot.add_cog(cog)
    bot.loop.create_task(cog.update_everything())
