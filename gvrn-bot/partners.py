import discord
from discord.ext import commands

DASH_EMOJI = "<:dot:1533231424532906014>"
ARROW_EMOJI = "<:arrow:1533216371326980266>"


class Partners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="partner0-20")
    @commands.has_permissions(administrator=True)
    async def partner_0_20(self, ctx):
        await ctx.send(
            f"{DASH_EMOJI} **0-20 Members** {ARROW_EMOJI} "
            f"You get no ping, we get here ping. - 3 members from your server join ours."
        )

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

    @commands.command(name="partner21-50")
    @commands.has_permissions(administrator=True)
    async def partner_21_50(self, ctx):
        await ctx.send(
            f"{DASH_EMOJI} **21-50 Members** {ARROW_EMOJI} "
            f"You get here ping, we get everyone ping. - 2 members join from your server."
        )

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

    @commands.command(name="partner51")
    @commands.has_permissions(administrator=True)
    async def partner_51(self, ctx):
        await ctx.send(
            f"{DASH_EMOJI} **51+ Members** {ARROW_EMOJI} "
            f"You get everyone ping, we get everyone ping."
        )

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass


async def setup(bot):
    await bot.add_cog(Partners(bot))
