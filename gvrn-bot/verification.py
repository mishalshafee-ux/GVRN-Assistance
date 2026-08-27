import os
import random
import re
import string

import aiohttp
import discord
from discord.ext import commands

COLOR = 0xE7F6FF

VERIFY_ROLE_ID = int(os.getenv("VERIFY_ROLE_ID", "0") or 0)
UNVERIFIED_ROLE_ID = int(os.getenv("UNVERIFIED_ROLE_ID", "0") or 0)

PENDING_VERIFICATIONS = {}


def make_code():
    letters = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"GVRN-{letters}"


def normalize_text(text):
    return re.sub(r"[^A-Z0-9]", "", text.upper())


async def get_roblox_user(username):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://users.roblox.com/v1/usernames/users",
            json={"usernames": [username], "excludeBannedUsers": False},
        ) as response:
            if response.status != 200:
                return None

            data = await response.json()
            users = data.get("data", [])

            if not users:
                return None

            return users[0]


async def get_roblox_bio(user_id):
    headers = {
        "User-Agent": "GVRN-Discord-Bot/1.0",
        "Accept": "application/json,text/html",
    }

    urls = [
        f"https://users.roblox.com/v1/users/{user_id}",
        f"https://users.roblox.com/v1/users/{user_id}?_={random.randint(100000, 999999)}",
    ]

    async with aiohttp.ClientSession(headers=headers) as session:
        for url in urls:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        continue

                    data = await response.json()
                    description = data.get("description", "")

                    if description:
                        return description
            except Exception:
                continue

        try:
            async with session.get(f"https://www.roblox.com/users/{user_id}/profile") as response:
                if response.status != 200:
                    return ""

                html = await response.text()

                patterns = [
                    r'"description":"(.*?)"',
                    r'"Description":"(.*?)"',
                    r'<meta name="description" content="(.*?)"',
                ]

                for pattern in patterns:
                    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                    if match:
                        description = match.group(1)
                        description = description.replace("\\n", "\n")
                        description = description.replace("\\u0026", "&")
                        description = description.replace("\\/", "/")
                        return description
        except Exception:
            return ""

    return ""


class VerifyModal(discord.ui.Modal, title="Verify Roblox Account"):
    roblox_username = discord.ui.TextInput(
        label="Roblox Username",
        placeholder="Enter your Roblox username",
        required=True,
        max_length=32,
    )

    async def on_submit(self, interaction: discord.Interaction):
        username = str(self.roblox_username.value).strip()
        roblox_user = await get_roblox_user(username)

        if not roblox_user:
            await interaction.response.send_message(
                "I could not find that Roblox username.",
                ephemeral=True,
            )
            return

        code = PENDING_VERIFICATIONS.get(interaction.user.id, {}).get("code") or make_code()

        PENDING_VERIFICATIONS[interaction.user.id] = {
            "code": code,
            "roblox_id": roblox_user["id"],
            "roblox_username": roblox_user["name"],
        }

        await interaction.response.send_message(
            (
                f"To verify **{roblox_user['name']}**, put this code in your Roblox profile About/Bio:\n\n"
                f"`{code}`\n\n"
                "After adding it, wait **30-90 seconds**, then click **I Added The Code** below.\n"
                "You can remove the code after you are verified."
            ),
            view=ConfirmVerifyView(),
            ephemeral=True,
        )


class ConfirmVerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)

    @discord.ui.button(
        label="I Added The Code",
        style=discord.ButtonStyle.success,
        custom_id="confirm_roblox_verify",
    )
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = PENDING_VERIFICATIONS.get(interaction.user.id)

        if not data:
            await interaction.response.send_message(
                "Please click Verify again and enter your Roblox username first.",
                ephemeral=True,
            )
            return

        bio = await get_roblox_bio(data["roblox_id"])
        needed_code = normalize_text(data["code"])
        visible_bio = normalize_text(bio)

        if needed_code not in visible_bio:
            preview = bio[:150] if bio else "empty bio"
            await interaction.response.send_message(
                (
                    "I still could not find the code in your Roblox About/Bio.\n"
                    "Make sure it is saved, wait **30-90 seconds**, then try again.\n\n"
                    f"Code I need: `{data['code']}`\n"
                    f"Bio I can currently see: `{preview}`"
                ),
                ephemeral=True,
            )
            return

        guild = interaction.guild
        civilian_role = guild.get_role(VERIFY_ROLE_ID)
        unverified_role = guild.get_role(UNVERIFIED_ROLE_ID)

        if civilian_role:
            await interaction.user.add_roles(civilian_role, reason="Roblox account verified.")

        if unverified_role and unverified_role in interaction.user.roles:
            await interaction.user.remove_roles(unverified_role, reason="Roblox account verified.")

        try:
            await interaction.user.edit(
                nick=f"{interaction.user.display_name} (@{data['roblox_username']})",
                reason="Roblox account verified.",
            )
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

        PENDING_VERIFICATIONS.pop(interaction.user.id, None)

        await interaction.response.send_message(
            f"✅ Verified as **{data['roblox_username']}**.",
            ephemeral=True,
        )


class VerifyPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.success,
        custom_id="open_verify_modal",
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(VerifyPanelView())

    @commands.command(name="verifypanel")
    @commands.has_permissions(manage_roles=True)
    async def verify_panel(self, ctx):
        embed = discord.Embed(
            title="✅ GVRN Verification",
            description=(
                "Welcome to **Greenville Roleplay Network**.\n\n"
                "To access the server, you must verify your Roblox account. "
                "Click the button below and enter your Roblox username.\n\n"
                "**How it works:**\n"
                "> 1. Click **Verify**.\n"
                "> 2. Enter your Roblox username.\n"
                "> 3. Add the code to your Roblox **About/Bio**.\n"
                "> 4. Click **I Added The Code**.\n\n"
                "After verification, you will receive the **Civilian** role and your "
                "**Unverified** role will be removed.\n\n"
                "You may remove the code from your Roblox bio after you are verified."
            ),
            color=COLOR,
        )
        embed.set_footer(text="GVRN Verification System")

        await ctx.send(embed=embed, view=VerifyPanelView())


async def setup(bot):
    await bot.add_cog(Verification(bot))
