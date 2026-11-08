import os

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands


GUILD_ID = int(os.getenv("GUILD_ID", "0") or 0)
CIVILIAN_ROLE_ID = int(os.getenv("CIVILIAN_ROLE_ID", "0") or 0)
UNVERIFIED_ROLE_ID = int(os.getenv("UNVERIFIED_ROLE_ID", "0") or 0)
BLOXLINK_API_KEY = os.getenv("BLOXLINK_API_KEY", "")

BLOXLINK_URL = (
    "https://api.blox.link/v4/public/discord-to-roblox/{discord_id}"
)
ROBLOX_URL = "https://users.roblox.com/v1/users/{roblox_id}"


def extract_roblox_id(data):
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


async def get_roblox_user(discord_id):
    headers = {}

    if BLOXLINK_API_KEY:
        headers["Authorization"] = BLOXLINK_API_KEY

    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(
            BLOXLINK_URL.format(discord_id=discord_id),
            headers=headers,
        ) as response:
            if response.status == 404:
                return None

            if response.status != 200:
                raise RuntimeError(
                    f"Bloxlink HTTP {response.status}"
                )

            bloxlink_data = await response.json(content_type=None)

        roblox_id = extract_roblox_id(bloxlink_data)

        if not roblox_id:
            return None

        async with session.get(
            ROBLOX_URL.format(roblox_id=roblox_id)
        ) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"Roblox HTTP {response.status}"
                )

            user_data = await response.json(content_type=None)

    return {
        "id": roblox_id,
        "username": user_data.get("name", "Unknown"),
        "display_name": user_data.get("displayName", "Unknown"),
    }


class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify Roblox",
        style=discord.ButtonStyle.primary,
        custom_id="gvrn:verify_roblox",
    )
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not interaction.guild:
            await interaction.response.send_message(
                "Use this button inside the server.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        member = interaction.user
        civilian_role = interaction.guild.get_role(CIVILIAN_ROLE_ID)
        unverified_role = interaction.guild.get_role(UNVERIFIED_ROLE_ID)

        if civilian_role is None:
            await interaction.followup.send(
                "The Civilian role is not configured.",
                ephemeral=True,
            )
            return

        try:
            roblox_user = await get_roblox_user(member.id)
        except Exception as error:
            print(f"Roblox verification error: {error}")
            await interaction.followup.send(
                "The verification service is temporarily unavailable.",
                ephemeral=True,
            )
            return

        if roblox_user is None:
            embed = discord.Embed(
                title="Roblox account not linked",
                description=(
                    "Link your Discord account with Bloxlink first, "
                    "then click this button again."
                ),
                color=0x7EC8E3,
            )
            await interaction.followup.send(
                embed=embed,
                ephemeral=True,
            )
            return

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
            await interaction.followup.send(
                "I found your Roblox account, but I cannot update your roles. "
                "Move my bot role above the verification roles.",
                ephemeral=True,
            )
            return

        nickname = f"[Civilian] {roblox_user['username']}"[:32]

        try:
            await member.edit(
                nick=nickname,
                reason="Successful Roblox verification",
            )
            nickname_message = f"Your nickname was changed to `{nickname}`."
        except discord.Forbidden:
            nickname_message = (
                "Your role was updated, but Discord prevented the nickname "
                "change because you may be an owner or administrator."
            )

        embed = discord.Embed(
            title="Verification successful",
            description=(
                f"Roblox account: **{roblox_user['username']}**\n"
                f"Display name: **{roblox_user['display_name']}**\n\n"
                "The Civilian role was added.\n"
                f"{nickname_message}"
            ),
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
        name="verification-panel",
        description="Send the Roblox verification panel.",
    )
    async def verification_panel(
        self,
        interaction: discord.Interaction,
    ):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "You need Manage Server permission.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="GVRN Roblox Verification",
            description=(
                "Click the button below to verify your linked Roblox "
                "account and receive the Civilian role."
            ),
            color=0x7EC8E3,
        )

        await interaction.response.send_message(
            embed=embed,
            view=VerificationView(),
        )


async def setup(bot):
    bot.add_view(VerificationView())
    await bot.add_cog(RobloxVerification(bot))
