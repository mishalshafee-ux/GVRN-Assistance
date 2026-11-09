import json
import os
from pathlib import Path
from urllib.parse import urlencode

import discord
from discord import app_commands
from discord.ext import commands


OAUTH_URL = os.getenv(
    "ROBLOX_OAUTH_AUTHORIZE_URL",
    "https://gvrn.wispbyte.app/roblox/authorize",
)
CIVILIAN_ROLE_ID = int(os.getenv("CIVILIAN_ROLE_ID", "0") or 0)
UNVERIFIED_ROLE_ID = int(os.getenv("UNVERIFIED_ROLE_ID", "0") or 0)

LINKS_FILE = (
    Path(__file__).resolve().parent.parent
    / "gvrn-session-site"
    / "data"
    / "roblox_links.json"
)


def verification_url(member_id):
    return f"{OAUTH_URL}?{urlencode({'discord_id': member_id})}"


async def apply_saved_verification(member):
    if not LINKS_FILE.exists():
        return

    try:
        links = json.loads(LINKS_FILE.read_text())
    except Exception:
        return

    account = links.get(str(member.id))

    if not account:
        return

    civilian = member.guild.get_role(CIVILIAN_ROLE_ID)
    unverified = member.guild.get_role(UNVERIFIED_ROLE_ID)

    if civilian is None:
        return

    try:
        await member.add_roles(civilian, reason="Saved Roblox verification")

        if unverified and unverified in member.roles:
            await member.remove_roles(
                unverified,
                reason="Saved Roblox verification",
            )

        nickname = f"[Civilian] {account['roblox_name']}"[:32]
        await member.edit(
            nick=nickname,
            reason="Saved Roblox verification",
        )
    except discord.Forbidden:
        print(f"Could not update verification roles for {member}")


class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify Roblox",
        style=discord.ButtonStyle.primary,
        custom_id="gvrn:roblox_oauth",
    )
    async def verify_button(self, interaction, button):
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Continue with Roblox",
                style=discord.ButtonStyle.link,
                url=verification_url(interaction.user.id),
            )
        )

        await interaction.response.send_message(
            "Click below to sign in with Roblox.",
            view=view,
            ephemeral=True,
        )


class RobloxVerification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="verify",
        description="Verify your Roblox account.",
    )
    async def verify(self, interaction):
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Continue with Roblox",
                style=discord.ButtonStyle.link,
                url=verification_url(interaction.user.id),
            )
        )

        await interaction.response.send_message(
            "Click below to sign in with Roblox.",
            view=view,
            ephemeral=True,
        )

    @commands.command(name="verifypanel")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def verifypanel(self, ctx):
        embed = discord.Embed(
            title="GVRN Roblox Verification",
            description=(
                "Click the button below to verify your Roblox account "
                "and receive the Civilian role."
            ),
            color=0x7EC8E3,
        )

        await ctx.send(embed=embed, view=VerificationView())

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await apply_saved_verification(member)


async def setup(bot):
    bot.add_view(VerificationView())
    await bot.add_cog(RobloxVerification(bot))
