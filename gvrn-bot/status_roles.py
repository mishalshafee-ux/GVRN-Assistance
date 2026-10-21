import discord
from discord.ext import commands

SUPPORTER_ROLE_ID = 1562448035970162708
ANNOUNCEMENT_CHANNEL_ID = 1531626313931034775


def has_gvrn_status(member):
    for activity in member.activities:
        if isinstance(activity, discord.CustomActivity):
            status_text = " ".join(
                str(value or "")
                for value in (
                    getattr(activity, "name", ""),
                    getattr(activity, "state", ""),
                )
            ).lower()

            if "gvrn" in status_text:
                return True

    return False


class StatusRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        role = after.guild.get_role(SUPPORTER_ROLE_ID)

        if role is None:
            return

        has_status = has_gvrn_status(after)
        already_has_role = role in after.roles

        if has_status and not already_has_role:
            try:
                await after.add_roles(role, reason="GVRN custom status supporter")
            except discord.Forbidden:
                print("Cannot add Server Contributor role. Check role hierarchy and Manage Roles.")
                return

            channel = after.guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)

            if channel:
                embed = discord.Embed(
                    title="Server Contributor",
                    description=(
                        f"{after.mention}, thank you for showing your support. "
                        f"By using GVRN in your custom status, you earned the "
                        f"**{role.name}** role."
                    ),
                    color=0xF5935F,
                )
                embed.set_footer(text="Greenville Roleplay Network")

                await channel.send(
                    content=after.mention,
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions(users=True),
                )

        elif not has_status and already_has_role:
            try:
                await after.remove_roles(
                    role,
                    reason="GVRN removed from custom status",
                )
            except discord.Forbidden:
                print("Cannot remove Server Contributor role. Check permissions.")


async def setup(bot):
    await bot.add_cog(StatusRoles(bot))
