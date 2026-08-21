import discord
from discord.ext import commands

COLOR = 0x76F55D


class CommandList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commands", aliases=["cmds", "helpme"])
    async def commands_list(self, ctx):
        embed = discord.Embed(
            title="GVRN Bot Commands",
            description="These commands work with both `!` and `?`.",
            color=COLOR,
        )

        embed.add_field(
            name="Panels",
            value=(
                "`!ticketpanel`\n"
                "`!verifypanel`\n"
                "`!lpanel`\n"
                "`!sessioninfo`\n"
                "`!GVRNad`"
            ),
            inline=False,
        )

        embed.add_field(
            name="Partner",
            value=(
                "`!partner0-20`\n"
                "`!partner21-50`\n"
                "`!partner51`"
            ),
            inline=False,
        )

        embed.add_field(
            name="Moderation / Logs",
            value=(
                "`?infraction1 <user/id> <reason>`\n"
                "`?infraction2 <user/id> <reason>`\n"
                "`?infraction3 <user/id> <reason>`\n"
                "`?modlog <user/id>`\n"
                "`?revoke <case> <reason>`\n"
                "`?edit <case> <new reason>`\n"
                "`!role <user/id> <role name> <reason>`"
            ),
            inline=False,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CommandList(bot))
