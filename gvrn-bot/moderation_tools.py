import os

import discord
from discord.ext import commands

GVRNAD_ROLE_ID = int(os.getenv("GVRNAD_ROLE_ID", "1531256052593459240") or 1531256052593459240)


def has_gvrnad_role():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True

        return any(role.id == GVRNAD_ROLE_ID for role in ctx.author.roles)

    return commands.check(predicate)


class ModerationTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", aliases=["clear"])
    @has_gvrnad_role()
    async def purge(self, ctx, amount: int):
        if amount < 1 or amount > 10000:
            await ctx.reply("Use an amount from `1` to `10000`.", mention_author=False)
            return

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        deleted = 0

        while amount > 0:
            chunk = min(amount, 100)
            deleted_messages = await ctx.channel.purge(limit=chunk)
            deleted += len(deleted_messages)
            amount -= chunk

        confirmation = await ctx.send(f"Deleted **{deleted}** message(s).")
        await confirmation.delete(delay=5)


async def setup(bot):
    await bot.add_cog(ModerationTools(bot))
