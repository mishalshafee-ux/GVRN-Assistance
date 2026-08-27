import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord.ext import commands

WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", "0"))
UNVERIFIED_ROLE_ID = int(os.getenv("UNVERIFIED_ROLE_ID", "0"))
ASSISTANCE_CHANNEL_ID = int(os.getenv("ASSISTANCE_CHANNEL_ID", "0"))
VERIFICATION_CHANNEL_ID = int(os.getenv("VERIFICATION_CHANNEL_ID", "0"))

WELCOME_CACHE_FILE = Path("welcome_cache.json")
WELCOME_DEDUPE = {}

SERVER_NAME = "GVRN"
WELCOME_COLOR = 0xD3E6FF
WELCOME_TITLE = "🌐 Welcome to GVRN!"


def load_cache():
    if not WELCOME_CACHE_FILE.exists():
        return {}

    with WELCOME_CACHE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_cache(cache):
    with WELCOME_CACHE_FILE.open("w", encoding="utf-8") as file:
        json.dump(cache, file, indent=2)


def recently_welcomed(member_id):
    now = datetime.now(timezone.utc)

    cached_timestamp = WELCOME_DEDUPE.get(member_id)
    if cached_timestamp and now - cached_timestamp < timedelta(minutes=10):
        return True

    cache = load_cache()
    timestamp = cache.get(str(member_id))

    if not timestamp:
        return False

    welcomed_at = datetime.fromisoformat(timestamp)
    return now - welcomed_at < timedelta(minutes=10)


def mark_welcomed(member_id):
    now = datetime.now(timezone.utc)
    WELCOME_DEDUPE[member_id] = now

    cache = load_cache()
    cache[str(member_id)] = now.isoformat()
    save_cache(cache)


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        unverified_role = member.guild.get_role(UNVERIFIED_ROLE_ID)
        if unverified_role:
            try:
                await member.add_roles(unverified_role, reason="New member joined.")
            except discord.Forbidden:
                pass

        if recently_welcomed(member.id):
            return

        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)

        if not isinstance(channel, discord.TextChannel):
            return

        assistance = f"<#{ASSISTANCE_CHANNEL_ID}>" if ASSISTANCE_CHANNEL_ID else "assistance"
        verification = f"<#{VERIFICATION_CHANNEL_ID}>" if VERIFICATION_CHANNEL_ID else "verification"

        embed = discord.Embed(
            title=WELCOME_TITLE,
            description=(
                f"> Welcome to **{SERVER_NAME}**. We are a community that strives for an enjoyable\n"
                f"> roleplay experience while keeping everything organized and professional.\n\n"
                f"> 🌐 Thank you for joining **{SERVER_NAME}**. We are excited to roleplay with you\n"
                f"> and we have a lot planned for the future, so make sure to stick around!\n\n"
                f"> 🤝 If you want to partner with us, open a ticket in {assistance}\n"
                f"> and our team will assist you.\n\n"
                f"> 🎫 If you require support, open a ticket in {assistance}.\n\n"
                f"> You are member **{member.guild.member_count}**. Thanks for joining!"
            ),
            color=WELCOME_COLOR,
        )

        mark_welcomed(member.id)
        await channel.send(content=member.mention, embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
