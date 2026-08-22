import discord
from discord.ext import commands

COLOR = 0x76F55D


class CommandList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commands", aliases=["cmds", "helpme", "command"])
    async def commands_list(self, ctx):
        embed = discord.Embed(
            title="GVRN Bot Commands",
            description="These commands work with both `!` and `?`.",
            color=COLOR,
        )

        embed.add_field(
            name="Panels",
            value=(
                "`!ticketpanel` - Sends the ticket panel\n"
                "`!verifypanel` - Sends the verify panel\n"
                "`!lpanel` - Sends application panel\n"
                "`!sessioninfo` - Sends session info panel\n"
                "`!GVRNad` - Sends GVRN advertisement"
            ),
            inline=False,
        )

        embed.add_field(
            name="Suggestions",
            value="`!suggest <idea>` - Sends a suggestion",
            inline=False,
        )

        embed.add_field(
            name="Partner",
            value=(
                "`!partner0-20` - Partnership requirement message\n"
                "`!partner21-50` - Partnership requirement message\n"
                "`!partner51` - Partnership requirement message\n"
                "Typing `partner` or `partnership` in a ticket shows requirements"
            ),
            inline=False,
        )

        embed.add_field(
            name="Tickets",
            value=(
                "Ticket dropdown creates tickets\n"
                "Staff can claim/unclaim tickets\n"
                "Closing tickets sends transcript to user\n"
                "Closing tickets logs transcript to server\n"
                "Users can rate support after close\n"
                "Low ratings ask what went wrong"
            ),
            inline=False,
        )

        embed.add_field(
            name="Vehicles",
            value=(
                "`/vehicle-registeration` - Register a vehicle\n"
                "`/vehicle-edit` - Edit a vehicle\n"
                "`/vehicle-delete` - Delete a vehicle\n"
                "`/my-profile` - View your profile\n"
                "`/profile-check` - Staff profile check\n"
                "`/license-set` - Set license status"
            ),
            inline=False,
        )

        embed.add_field(
            name="Sessions",
            value=(
                "`/session startup` - Start session vote\n"
                "`/ea` - Early access session\n"
                "`/release` - Release session\n"
                "`/regen` - Link regeneration notice\n"
                "`/re-invites` - Re-invites notice\n"
                "`/over` - End session"
            ),
            inline=False,
        )

        embed.add_field(
            name="Applications",
            value=(
                "`!lpanel` - Application panel\n"
                "`!appstatus license open/closed`\n"
                "`!appstatus staff open/closed`\n"
                "`!appstatus appeal open/closed`"
            ),
            inline=False,
        )

        embed.add_field(
            name="Infractions",
            value=(
                "`?infraction1 <user/id> <reason>`\n"
                "`?infraction2 <user/id> <reason>`\n"
                "`?infraction3 <user/id> <reason>`\n"
                "`?modlog <user/id>`\n"
                "`?revoke <case> <reason>`\n"
                "`?edit <case> <new reason>`"
            ),
            inline=False,
        )

        embed.add_field(
            name="Staff Tools",
            value=(
                "`!role <user/id> <role name> <reason>`\n"
                "`/say` - Make bot say a message\n"
                "`/staff-adjustment` - Staff adjustment message"
            ),
            inline=False,
        )

        embed.add_field(
            name="Server Stats",
            value="Auto-updates member count and bot count channels.",
            inline=False,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CommandList(bot))
