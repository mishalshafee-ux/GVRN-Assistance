import os

import discord
from discord.ext import commands

WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", "0"))
ASSISTANCE_CHANNEL_ID = int(os.getenv("ASSISTANCE_CHANNEL_ID", "0"))
VERIFICATION_CHANNEL_ID = int(os.getenv("VERIFICATION_CHANNEL_ID", "0"))

# =========================
# WELCOME MESSAGE EDIT AREA
# =========================

SERVER_NAME = "GVRN"
WELCOME_COLOR = 0x76F55D

WELCOME_TITLE = "🌐 Welcome to GVRN!"

# =========================
# END WELCOME MESSAGE EDIT AREA
# =========================


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)

        if not isinstance(channel, discord.TextChannel):
            return

        assistance = f"<#{ASSISTANCE_CHANNEL_ID}>" if ASSISTANCE_CHANNEL_ID else "assistance"
        verification = f"<#{VERIFICATION_CHANNEL_ID}>" if VERIFICATION_CHANNEL_ID else "verification"

        embed = discord.Embed(
            title=WELCOME_TITLE,
            description=(
                f"> 🌐 Welcome to **{SERVER_NAME}**. We are a community that strives for an enjoyable "
                f"roleplay experience while keeping everything organized and professional.\n\n"
                f">  Thank you for joining **{SERVER_NAME}**. We are excited to roleplay with you and "
                f"we have a lot planned for the future, so make sure to stick around!\n\n"
                f"> ❔ If you require support or want to partner, open a ticket in {assistance} "
                f"and our team will assist you.\n\n"
                f"> 👥 Please make sure to verify yourself in {verification} to gain access to the rest of the server.\n\n"
                f"> -# You are member **{member.guild.member_count}**. Thanks for joining!"
            ),
            color=WELCOME_COLOR,
        )

        await channel.send(content=member.mention, embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
