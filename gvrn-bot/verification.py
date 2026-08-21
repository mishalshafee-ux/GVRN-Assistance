import os
import random
import string

import aiohttp
import discord
from discord.ext import commands

VERIFY_ROLE_ID = int(os.getenv("VERIFY_ROLE_ID", "0"))
UNVERIFIED_ROLE_ID = int(os.getenv("UNVERIFIED_ROLE_ID", "0"))

SERVER_NAME = "GVRN"
VERIFY_COLOR = 0x76F55D
VERIFY_TITLE = "GVRN Verification"
VERIFY_DESCRIPTION = (
    "Welcome to **GVRN**.\n\n"
    "Click the button below to verify your Roblox account and gain access."
)
VERIFY_BUTTON_LABEL = "Verify"

PENDING_VERIFICATIONS = {}


async def get_roblox_user(username: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://users.roblox.com/v1/usernames/users",
            json={"usernames": [username], "excludeBannedUsers": True},
        ) as response:
            data = await response.json()

        users = data.get("data", [])
        if not users:
            return None

        user_id = users[0]["id"]

        async with session.get(f"https://users.roblox.com/v1/users/{user_id}") as response:
            profile = await response.json()

    return profile


def make_code():
    letters = string.ascii_uppercase + string.digits
    return "GVRN-" + "".join(random.choice(letters) for _ in range(6))


def normalize_code_text(value: str):
    return "".join(character for character in value.upper() if character.isalnum())


class RobloxUsernameModal(discord.ui.Modal, title="Roblox Verification"):
    roblox_username = discord.ui.TextInput(
        label="Roblox Username",
        placeholder="Example: Mishal734567",
        max_length=32,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        username = str(self.roblox_username.value).strip().replace("@", "")
        profile = await get_roblox_user(username)

        if not profile:
            await interaction.response.send_message(
                "I could not find that Roblox username.",
                ephemeral=True,
            )
            return

        pending = PENDING_VERIFICATIONS.get(interaction.user.id)

        if pending and pending.get("roblox_username", "").lower() == profile["name"].lower():
            code = pending["code"]
        else:
            code = make_code()

        PENDING_VERIFICATIONS[interaction.user.id] = {
            "code": code,
            "roblox_id": profile["id"],
            "roblox_username": profile["name"],
        }

        await interaction.response.send_message(
            (
                f"To verify **{profile['name']}**, put this code in your Roblox profile About/Bio:\n\n"
                f"`{code}`\n\n"
                f"After adding it, click **I Added The Code** below."
            ),
            view=ConfirmRobloxView(),
            ephemeral=True,
        )


class ConfirmRobloxView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)

    @discord.ui.button(label="I Added The Code", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        pending = PENDING_VERIFICATIONS.get(interaction.user.id)

        if not pending:
            await interaction.response.send_message("Start verification again.", ephemeral=True)
            return

        profile = await get_roblox_user(pending["roblox_username"])

        if not profile:
            await interaction.response.send_message("Could not check your Roblox profile.", ephemeral=True)
            return

        description = profile.get("description", "")

        saved_code = pending["code"].upper().replace(" ", "")
        profile_text = description.upper().replace(" ", "")

        if saved_code not in profile_text:
            await interaction.response.send_message(
                "I could not find the code in your Roblox About/Bio yet. Make sure it is saved, then wait 30-90 seconds and try again.",
                ephemeral=True,
            )
            return

        civilian_role = interaction.guild.get_role(VERIFY_ROLE_ID)
        unverified_role = interaction.guild.get_role(UNVERIFIED_ROLE_ID)

        if civilian_role is None:
            await interaction.response.send_message("Civilian role was not found.", ephemeral=True)
            return

        new_nickname = f"{interaction.user.display_name} (@{profile['name']})"[:32]

        try:
            await interaction.user.add_roles(civilian_role, reason="Roblox profile verified.")
            if unverified_role and unverified_role in interaction.user.roles:
                await interaction.user.remove_roles(unverified_role, reason="Roblox profile verified.")
            await interaction.user.edit(nick=new_nickname, reason="Roblox profile verified.")
        except discord.Forbidden:
            await interaction.response.send_message(
                "I cannot update your roles or nickname. Check my role position and permissions.",
                ephemeral=True,
            )
            return

        PENDING_VERIFICATIONS.pop(interaction.user.id, None)

        await interaction.response.send_message(
            f"You have been verified as `{new_nickname}`. You can remove the code from your Roblox profile now.",
            ephemeral=True,
        )


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=VERIFY_BUTTON_LABEL, style=discord.ButtonStyle.success, custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RobloxUsernameModal())


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(VerifyView())

    @commands.command(name="verifypanel")
    @commands.has_permissions(administrator=True)
    async def verifypanel(self, ctx):
        embed = discord.Embed(title=VERIFY_TITLE, description=VERIFY_DESCRIPTION, color=VERIFY_COLOR)
        embed.set_footer(text=f"{SERVER_NAME} Verification")
        await ctx.send(embed=embed, view=VerifyView())

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass


async def setup(bot):
    await bot.add_cog(Verification(bot))
