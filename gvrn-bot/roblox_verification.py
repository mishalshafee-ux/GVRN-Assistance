import os

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands


CIVILIAN_ROLE_ID = int(os.getenv("CIVILIAN_ROLE_ID", "0") or 0)
UNVERIFIED_ROLE_ID = int(os.getenv("UNVERIFIED_ROLE_ID", "0") or 0)
BLOXLINK_API_KEY = os.getenv("BLOXLINK_API_KEY", "")

BLOXLINK_URL = (
    "https://api.blox.link/v4/public/guilds/"
    "{guild_id}/discord-to-roblox/{discord_id}"
)
ROBLOX_URL = "https://users.roblox.com/v1/users/{roblox_id}"


def get_roblox_id(data):
    if not isinstance(data, dict):
        return None

    for key in ("robloxID", "robloxId", "roblox_id", "robloxUserId"):
        value = data.get(key)
        if value:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

    return None


async def get_roblox_user(guild_id, discord_id):
    headers = {}

    if BLOXLINK_API_KEY:
        headers["Authorization"] = BLOXLINK_API_KEY

    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(
            BLOXLINK_URL.format(
                guild_id=guild_id,
                discord_id=discord_id,
            ),
            headers=headers,
        ) as response:
            if response.status == 404:
                return None

            if response.status != 200:
                raise RuntimeError(
                    f"Bloxlink returned HTTP {response.status}"
                )

            data = await response.json(content_type=None)

        roblox_id = get_roblox_id(data)

        if not roblox_id:
            return None

        async with session.get(
            ROBLOX_URL.format(roblox_id=roblox_id)
        ) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"Roblox returned HTTP {response.status}"
                )

            user_data = await response.json(content_type=None)

    return {
        "username": user_data.get("name", "Unknown"),
        "display_name": user_data.get("displayName", "Unknown"),
    }


async def verify_member(member):
    guild = member.guild
    civilian_role = guild.get_role(CIVILIAN_ROLE_ID)
    unverified_role = guild.get_role(UNVERIFIED_ROLE_ID)

    if civilian_role is None:
        return False, "The Civilian role is not configured."

    try:
        roblox_user = await get_roblox_user(guild.id, member.id)
    except Exception as error:
        print(f"Bloxlink verification error: {error}")
        return False, "The verification service is temporarily unavailable."

    if roblox_user is None:
        return False, (
            "Your Discord account is not linked to Roblox through Bloxlink. "
            "Link your account first, then try again."
        )

    try:
        await member.add_roles(
            civilian_role,
            reason="Successful Roblox verification",
        )

        if unverified_role and unverified_role in member.roles:
            await member.remove_roles(
                unverified_role,
                reason="Successful Roblox verification",
            )
    except discord.Forbidden:
        return False, (
            "I found your Roblox account, but I cannot update your roles. "
            "Move the bot role above Civilian and Unverified."
        )

    nickname = f"[Civilian] {roblox_user['username']}"[:32]

    try:
        await member.edit(
            nick=nickname,
            reason="Successful Roblox verification",
        )
    except discord.Forbidden:
        return True, (
            f"Verified as **{roblox_user['username']}** and added the "
            "Civilian role. Discord prevented the nickname change."
        )

    return True, (
        f"Verified as **{roblox_user['username']}** and added the "
        f" nickname `{nickname}`."
    )


class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify Roblox",
        style=discord.ButtonStyle.primary,
        custom_id="gvrn:verify_roblox",
    )
    async def verify_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.defer(ephemeral=True)

        success, message = await verify_member(interaction.user)

        embed = discord.Embed(
            title="Verification" if success else "Verification unavailable",
            description=message,
            color=0x7EC8E3,
        )

        await interaction.followup.send(
            embed=embed,
            ephemeral=True,
        )


class RobloxVerification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="verify",
        description="Verify your linked Roblox account.",
    )
    async def verify(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        success, message = await verify_member(interaction.user)

        embed = discord.Embed(
            title="Verification" if success else "Verification unavailable",
            description=message,
            color=0x7EC8E3,
        )

        await interaction.followup.send(
            embed=embed,
            ephemeral=True,
        )

    @commands.command(name="verifypanel")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def verify_panel(self, ctx):
        embed = discord.Embed(
            title="GVRN Roblox Verification",
            description=(
                "Click the button below to verify your linked Roblox "
                "account and receive the Civilian role."
            ),
            color=0x7EC8E3,
        )

        await ctx.send(
            embed=embed,
            view=VerificationView(),
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            success, message = await verify_member(member)

            if success:
                print(
                    f"Auto-verified {member} in {member.guild}: {message}"
                )
        except Exception as error:
            print(f"Join verification error: {error}")


async def setup(bot):
    bot.add_view(VerificationView())
    await bot.add_cog(RobloxVerification(bot))
