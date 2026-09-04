import json
import os
import uuid
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
        data = json.load(file)

    changed = False

    for user_data in data.get("users", {}).values():
        user_data.setdefault("has_license", False)
        user_data.setdefault("vehicles", [])

        for vehicle in user_data["vehicles"]:
            if "id" not in vehicle:
                vehicle["id"] = uuid.uuid4().hex[:8]
                changed = True

    if changed:
        save_data(data)

    return data


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


def find_vehicle_by_id(vehicles, vehicle_id):
    for vehicle in vehicles:
        if vehicle.get("id") == vehicle_id:
            return vehicle

    return None


def vehicle_choice_name(vehicle):
    return f"{vehicle['year']} {vehicle['make']} | {vehicle['colour']} | {vehicle['plate']}"[:100]


async def vehicle_autocomplete(interaction: discord.Interaction, current: str):
    data = load_data()
    user_data = get_user_data(data, interaction.user.id)

    choices = []

    for vehicle in user_data["vehicles"]:
        name = vehicle_choice_name(vehicle)

        if current.lower() in name.lower():
            choices.append(
                app_commands.Choice(
                    name=name,
                    value=vehicle["id"],
                )
            )

    return choices[:25]


class VehicleRegisterModal(discord.ui.Modal, title="Vehicle Registration"):
    colour = discord.ui.TextInput(label="Vehicle Colour", placeholder="Example: Black", max_length=50)
    make = discord.ui.TextInput(label="Vehicle Make", placeholder="Example: Ford Crown Victoria", max_length=80)
    year = discord.ui.TextInput(label="Vehicle Year", placeholder="Example: 2011", max_length=4)
    plate = discord.ui.TextInput(label="Vehicle Plate", placeholder="Example: GVRN123", max_length=20)

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        user_data = get_user_data(data, interaction.user.id)

        vehicle = {
            "id": uuid.uuid4().hex[:8],
            "colour": str(self.colour.value).strip(),
            "make": str(self.make.value).strip(),
            "year": str(self.year.value).strip(),
            "plate": str(self.plate.value).upper().strip(),
        }

        user_data["vehicles"].append(vehicle)
        save_data(data)

        embed = discord.Embed(title="Vehicle Registered", color=0xEAC5FD)
        embed.add_field(name="Colour", value=vehicle["colour"], inline=True)
        embed.add_field(name="Make", value=vehicle["make"], inline=True)
        embed.add_field(name="Year", value=vehicle["year"], inline=True)
        embed.add_field(name="Plate", value=vehicle["plate"], inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)


class VehicleEditModal(discord.ui.Modal, title="Edit Vehicle Registration"):
    def __init__(self, vehicle_id, vehicle):
        super().__init__()
        self.vehicle_id = vehicle_id

        self.colour = discord.ui.TextInput(label="Vehicle Colour", default=vehicle["colour"], max_length=50)
        self.make = discord.ui.TextInput(label="Vehicle Make", default=vehicle["make"], max_length=80)
        self.year = discord.ui.TextInput(label="Vehicle Year", default=vehicle["year"], max_length=4)
        self.plate = discord.ui.TextInput(label="Vehicle Plate", default=vehicle["plate"], max_length=20)

        self.add_item(self.colour)
        self.add_item(self.make)
        self.add_item(self.year)
        self.add_item(self.plate)

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        user_data = get_user_data(data, interaction.user.id)
        vehicle = find_vehicle_by_id(user_data["vehicles"], self.vehicle_id)

        if not vehicle:
            await interaction.response.send_message("That vehicle could not be found.", ephemeral=True)
            return

        vehicle["colour"] = str(self.colour.value).strip()
        vehicle["make"] = str(self.make.value).strip()
        vehicle["year"] = str(self.year.value).strip()
        vehicle["plate"] = str(self.plate.value).upper().strip()

        save_data(data)

        await interaction.response.send_message(
            f"Updated vehicle: `{vehicle_choice_name(vehicle)}`.",
            ephemeral=True,
        )


class VehicleRegistration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="vehicle-registeration", description="Register a vehicle.")
    async def vehicle_registeration(self, interaction: discord.Interaction):
        await interaction.response.send_modal(VehicleRegisterModal())

    @app_commands.command(name="vehicle-edit", description="Edit one of your registered vehicles.")
    @app_commands.describe(vehicle="Choose which vehicle you want to edit")
    @app_commands.autocomplete(vehicle=vehicle_autocomplete)
    async def vehicle_edit(self, interaction: discord.Interaction, vehicle: str):
        data = load_data()
        user_data = get_user_data(data, interaction.user.id)
        selected_vehicle = find_vehicle_by_id(user_data["vehicles"], vehicle)

        if not selected_vehicle:
            await interaction.response.send_message("That vehicle could not be found.", ephemeral=True)
            return

        await interaction.response.send_modal(VehicleEditModal(vehicle, selected_vehicle))

    @app_commands.command(name="vehicle-delete", description="Delete one of your registered vehicles.")
    @app_commands.describe(vehicle="Choose which vehicle you want to delete")
    @app_commands.autocomplete(vehicle=vehicle_autocomplete)
    async def vehicle_delete(self, interaction: discord.Interaction, vehicle: str):
        data = load_data()
        user_data = get_user_data(data, interaction.user.id)
        selected_vehicle = find_vehicle_by_id(user_data["vehicles"], vehicle)

        if not selected_vehicle:
            await interaction.response.send_message("That vehicle could not be found.", ephemeral=True)
            return

        user_data["vehicles"].remove(selected_vehicle)
        save_data(data)

        await interaction.response.send_message(
            f"Deleted vehicle: `{vehicle_choice_name(selected_vehicle)}`.",
            ephemeral=True,
        )

    @app_commands.command(name="my-profile", description="View your license and registered vehicles.")
    async def my_profile(self, interaction: discord.Interaction):
        data = load_data()
        user_data = get_user_data(data, interaction.user.id)

        embed = self.build_profile_embed(interaction.user, user_data)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="profile-check", description="Police command: check a user's license and registered vehicles.")
    @app_commands.describe(user="User to check")
    async def profile_check(self, interaction: discord.Interaction, user: discord.Member):
        if not is_police_or_admin(interaction.user):
            await interaction.response.send_message("You need the police role to use this command.", ephemeral=True)
            return

        data = load_data()
        user_data = get_user_data(data, user.id)

        embed = self.build_profile_embed(user, user_data)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="license-set", description="Police command: set whether a user has a license.")
    @app_commands.describe(user="User to update", has_license="Does this user have a license?")
    async def license_set(self, interaction: discord.Interaction, user: discord.Member, has_license: bool):
        if not is_police_or_admin(interaction.user):
            await interaction.response.send_message("You need the police role to use this command.", ephemeral=True)
            return

        data = load_data()
        user_data = get_user_data(data, user.id)
        user_data["has_license"] = has_license
        save_data(data)

        status = "has a valid license" if has_license else "does not have a valid license"
        await interaction.response.send_message(f"{user.mention} now {status}.", ephemeral=True)

    def build_profile_embed(self, user, user_data):
        license_status = "Valid" if user_data["has_license"] else "No License"

        embed = discord.Embed(title=f"{user.display_name}'s Vehicle Profile", color=0xEAC5FD)
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

        embed.add_field(name="Registered Vehicles", value="\n\n".join(vehicle_lines), inline=False)
        return embed


async def setup(bot):
    await bot.add_cog(VehicleRegistration(bot))
