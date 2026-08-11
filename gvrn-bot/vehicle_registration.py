import json
import os
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

DATA_FILE = Path("vehicle_data.json")
POLICE_ROLE_ID = int(os.getenv("POLICE_ROLE_ID", "0"))


def load_data():
    if not DATA_FILE.exists():
        return {"users": {}}

    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def get_user_data(data, user_id):
    user_id = str(user_id)

    if user_id not in data["users"]:
        data["users"][user_id] = {
            "has_license": False,
            "vehicles": [],
        }

    return data["users"][user_id]


def is_police_or_admin(member):
    if member.guild_permissions.administrator:
        return True

    return any(role.id == POLICE_ROLE_ID for role in member.roles)


def find_vehicle(vehicles, plate):
    plate = plate.upper().strip()

    for vehicle in vehicles:
        if vehicle["plate"].upper() == plate:
            return vehicle

    return None


class VehicleRegisterModal(discord.ui.Modal, title="Vehicle Registration"):
    colour = discord.ui.TextInput(
        label="Vehicle Colour",
        placeholder="Example: Black",
        max_length=50,
    )
    make = discord.ui.TextInput(
        label="Vehicle Make",
        placeholder="Example: Ford Crown Victoria",
        max_length=80,
    )
    year = discord.ui.TextInput(
        label="Vehicle Year",
        placeholder="Example: 2011",
        max_length=4,
    )
    plate = discord.ui.TextInput(
        label="Vehicle Plate",
        placeholder="Example: GVRN123",
        max_length=20,
    )

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        user_data = get_user_data(data, interaction.user.id)

        plate = str(self.plate.value).upper().strip()

        if find_vehicle(user_data["vehicles"], plate):
            await interaction.response.send_message(
                f"You already have a vehicle registered with plate `{plate}`.",
                ephemeral=True,
            )
            return

        vehicle = {
            "colour": str(self.colour.value).strip(),
            "make": str(self.make.value).strip(),
            "year": str(self.year.value).strip(),
            "plate": plate,
        }

        user_data["vehicles"].append(vehicle)
        save_data(data)

        embed = discord.Embed(
            title="Vehicle Registered",
            color=0x76F55D,
        )
        embed.add_field(name="Colour", value=vehicle["colour"], inline=True)
        embed.add_field(name="Make", value=vehicle["make"], inline=True)
        embed.add_field(name="Year", value=vehicle["year"], inline=True)
        embed.add_field(name="Plate", value=vehicle["plate"], inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)


class VehicleEditModal(discord.ui.Modal, title="Edit Vehicle Registration"):
    def __init__(self, old_plate):
        super().__init__()
        self.old_plate = old_plate.upper().strip()

        self.colour = discord.ui.TextInput(label="New Vehicle Colour", max_length=50)
        self.make = discord.ui.TextInput(label="New Vehicle Make", max_length=80)
        self.year = discord.ui.TextInput(label="New Vehicle Year", max_length=4)
        self.plate = discord.ui.TextInput(label="New Vehicle Plate", max_length=20)

        self.add_item(self.colour)
        self.add_item(self.make)
        self.add_item(self.year)
        self.add_item(self.plate)

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        user_data = get_user_data(data, interaction.user.id)
        vehicle = find_vehicle(user_data["vehicles"], self.old_plate)

        if not vehicle:
            await interaction.response.send_message(
                f"No vehicle found with plate `{self.old_plate}`.",
                ephemeral=True,
            )
            return

        vehicle["colour"] = str(self.colour.value).strip()
        vehicle["make"] = str(self.make.value).strip()
        vehicle["year"] = str(self.year.value).strip()
        vehicle["plate"] = str(self.plate.value).upper().strip()

        save_data(data)

        await interaction.response.send_message(
            f"Vehicle `{self.old_plate}` has been updated to `{vehicle['plate']}`.",
            ephemeral=True,
        )


class VehicleRegistration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="vehicle-registeration",
        description="Register a vehicle.",
    )
    async def vehicle_registeration(self, interaction: discord.Interaction):
        await interaction.response.send_modal(VehicleRegisterModal())

    @app_commands.command(
        name="vehicle-edit",
        description="Edit one of your registered vehicles.",
    )
    @app_commands.describe(plate="Plate of the vehicle you want to edit")
    async def vehicle_edit(self, interaction: discord.Interaction, plate: str):
        await interaction.response.send_modal(VehicleEditModal(plate))

    @app_commands.command(
        name="vehicle-delete",
        description="Delete one of your registered vehicles.",
    )
    @app_commands.describe(plate="Plate of the vehicle you want to delete")
    async def vehicle_delete(self, interaction: discord.Interaction, plate: str):
        data = load_data()
        user_data = get_user_data(data, interaction.user.id)

        vehicle = find_vehicle(user_data["vehicles"], plate)

        if not vehicle:
            await interaction.response.send_message(
                f"No vehicle found with plate `{plate.upper()}`.",
                ephemeral=True,
            )
            return

        user_data["vehicles"].remove(vehicle)
        save_data(data)

        await interaction.response.send_message(
            f"Deleted vehicle with plate `{vehicle['plate']}`.",
            ephemeral=True,
        )

    @app_commands.command(
        name="my-profile",
        description="View your license and registered vehicles.",
    )
    async def my_profile(self, interaction: discord.Interaction):
        data = load_data()
        user_data = get_user_data(data, interaction.user.id)

        embed = self.build_profile_embed(interaction.user, user_data)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="profile-check",
        description="Police command: check a user's license and registered vehicles.",
    )
    @app_commands.describe(user="User to check")
    async def profile_check(self, interaction: discord.Interaction, user: discord.Member):
        if not is_police_or_admin(interaction.user):
            await interaction.response.send_message(
                "You need the police role to use this command.",
                ephemeral=True,
            )
            return

        data = load_data()
        user_data = get_user_data(data, user.id)

        embed = self.build_profile_embed(user, user_data)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="license-set",
        description="Police command: set whether a user has a license.",
    )
    @app_commands.describe(user="User to update", has_license="Does this user have a license?")
    async def license_set(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        has_license: bool,
    ):
        if not is_police_or_admin(interaction.user):
            await interaction.response.send_message(
                "You need the police role to use this command.",
                ephemeral=True,
            )
            return

        data = load_data()
        user_data = get_user_data(data, user.id)
        user_data["has_license"] = has_license
        save_data(data)

        status = "has a valid license" if has_license else "does not have a valid license"

        await interaction.response.send_message(
            f"{user.mention} now {status}.",
            ephemeral=True,
        )

    def build_profile_embed(self, user, user_data):
        license_status = "Valid" if user_data["has_license"] else "No License"

        embed = discord.Embed(
            title=f"{user.display_name}'s Vehicle Profile",
            color=0x76F55D,
        )
        embed.add_field(name="License Status", value=license_status, inline=False)

        vehicles = user_data["vehicles"]

        if not vehicles:
            embed.add_field(name="Registered Vehicles", value="No vehicles registered.", inline=False)
            return embed

        vehicle_lines = []

        for index, vehicle in enumerate(vehicles, start=1):
            vehicle_lines.append(
                f"**{index}. {vehicle['plate']}**\n"
                f"Colour: {vehicle['colour']}\n"
                f"Make: {vehicle['make']}\n"
                f"Year: {vehicle['year']}"
            )

        embed.add_field(
            name="Registered Vehicles",
            value="\n\n".join(vehicle_lines),
            inline=False,
        )

        return embed


async def setup(bot):
    await bot.add_cog(VehicleRegistration(bot))
