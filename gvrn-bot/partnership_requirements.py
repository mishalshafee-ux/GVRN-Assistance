import os
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

DOT_EMOJI = os.getenv("PARTNER_DOT_EMOJI", "<:dot:1533231424532906014>")
ARROW_EMOJI = os.getenv("PARTNER_ARROW_EMOJI", "<:arrow:1533216371326980266>")

TICKET_CATEGORY_IDS = {
    int(os.getenv("MARKETPLACE_TICKET_CATEGORY_ID", "0")),
    int(os.getenv("GENERAL_TICKET_CATEGORY_ID", "0")),
    int(os.getenv("REPORT_TICKET_CATEGORY_ID", "0")),
}

COOLDOWN = {}
COOLDOWN_SECONDS = 300


def is_ticket_channel(channel: discord.abc.GuildChannel):
    if not isinstance(channel, discord.TextChannel):
        return False

    if channel.topic and channel.topic.startswith("ticket-owner:"):
        return True

    if channel.category_id in TICKET_CATEGORY_IDS:
        return True

    return False


def requirements_text():
    return (
        "**Partnership Requirements**\n\n"
        f"{DOT_EMOJI} **0-20 Members** {ARROW_EMOJI} You get no ping, we get here ping. "
        "- 3 members from your server join ours.\n\n"
        f"{DOT_EMOJI} **21-50 Members** {ARROW_EMOJI} You get here ping, we get everyone ping. "
        "- 2 members join from your server.\n\n"
        f"{DOT_EMOJI} **51+ Members** {ARROW_EMOJI} You get everyone ping, we get everyone ping."
    )


class PartnershipRequirements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        content = message.content.lower()

        if "partnership" not in content and "partner" not in content:
            return

        if not is_ticket_channel(message.channel):
            return

        key = (message.guild.id, message.channel.id, message.author.id)
        now = datetime.now(timezone.utc)

        if key in COOLDOWN and now - COOLDOWN[key] < timedelta(seconds=COOLDOWN_SECONDS):
            return

        COOLDOWN[key] = now
        await message.reply(requirements_text(), mention_author=False)


async def setup(bot):
    await bot.add_cog(PartnershipRequirements(bot))
