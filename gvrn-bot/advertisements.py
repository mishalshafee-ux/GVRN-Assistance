import discord
from discord.ext import commands

OGVRN_AD_MESSAGE = """
# Official Greenville Roleplay Network

### "The Future of Roleplays."

Looking for a Greenville roleplay community where realism meets excitement? Your next roleplay experience starts here!

Welcome to Official Greenville Roleplay Network, a growing community dedicated to creating immersive, realistic, and enjoyable roleplay experiences.

Whether you're looking to serve and protect, build your career, or simply enjoy quality roleplays with others, there's a place for you here!

**What we offer**

- Realistic Roleplays — Enjoy organised scenarios and immersive experiences.
- Professional Staff Team — A team dedicated to keeping the community running smoothly.
- Friendly Community — Meet new people, make friends, and become part of something bigger.

**We're Recruiting!**

We're currently looking for:

- Dedicated and active staff members
- Enthusiastic roleplayers

[Make sure to join our community](https://www.roblox.com/share/g/56603729)

Join [Official Greenville Roleplay Network today!](https://discord.gg/yps5DZE824)
"""


class Advertisements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="OGVRNad", aliases=["gvrnad"])
    @commands.check(lambda ctx: ctx.author.guild_permissions.administrator or any(role.id == 1531256052593459240 for role in ctx.author.roles))
    async def gvrn_ad(self, ctx):
        await ctx.send(OGVRN_AD_MESSAGE)

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass


async def setup(bot):
    await bot.add_cog(Advertisements(bot))
