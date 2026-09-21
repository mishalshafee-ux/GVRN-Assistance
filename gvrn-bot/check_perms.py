import discord
from discord.ext import commands


class CheckPerms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="checkslashperms")
    @commands.has_permissions(administrator=True)
    async def checkslashperms(self, ctx):
        allowed = []
        denied = []

        for member in ctx.guild.members:
            if member.bot:
                continue

            perms = ctx.channel.permissions_for(member)
            if perms.use_application_commands:
                allowed.append(member.display_name)
            else:
                denied.append(member.display_name)

        allowed_text = "\n".join(allowed[:50]) or "None"
        denied_text = "\n".join(denied[:50]) or "None"

        embed = discord.Embed(
            title="Slash Command Permission Check",
            color=0xEAC5FD,
        )
        embed.add_field(name=f"Can Use Slash Commands ({len(allowed)})", value=allowed_text, inline=False)
        embed.add_field(name=f"Cannot Use Slash Commands ({len(denied)})", value=denied_text, inline=False)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CheckPerms(bot))
