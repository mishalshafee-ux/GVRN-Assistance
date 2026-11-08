import re
import discord
from discord import app_commands
from discord.ext import commands

EMBED_COLOR = 0x7EC8E3


def staff_only(interaction: discord.Interaction):
    return interaction.user.guild_permissions.manage_channels


class ExtraCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ticket = app_commands.Group(
        name="ticket",
        description="Manage the current ticket.",
    )

    @ticket.command(name="add", description="Add a member to this ticket.")
    @app_commands.describe(member="Member to add")
    async def ticket_add(self, interaction: discord.Interaction, member: discord.Member):
        if not staff_only(interaction):
            await interaction.response.send_message(
                "You need Manage Channels permission.",
                ephemeral=True,
            )
            return

        await interaction.channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        )
        await interaction.response.send_message(
            f"{member.mention} was added to this ticket."
        )

    @ticket.command(name="remove", description="Remove a member from this ticket.")
    @app_commands.describe(member="Member to remove")
    async def ticket_remove(self, interaction: discord.Interaction, member: discord.Member):
        if not staff_only(interaction):
            await interaction.response.send_message(
                "You need Manage Channels permission.",
                ephemeral=True,
            )
            return

        await interaction.channel.set_permissions(
            member,
            view_channel=False,
            send_messages=False,
        )
        await interaction.response.send_message(
            f"{member.mention} was removed from this ticket."
        )

    @ticket.command(name="rename", description="Rename this ticket.")
    @app_commands.describe(name="New ticket name")
    async def ticket_rename(self, interaction: discord.Interaction, name: str):
        if not staff_only(interaction):
            await interaction.response.send_message(
                "You need Manage Channels permission.",
                ephemeral=True,
            )
            return

        clean_name = re.sub(r"[^a-zA-Z0-9-]", "-", name.lower()).strip("-")

        if not clean_name:
            await interaction.response.send_message(
                "Enter a valid channel name.",
                ephemeral=True,
            )
            return

        await interaction.channel.edit(name=clean_name[:100])
        await interaction.response.send_message(
            f"Ticket renamed to `{clean_name[:100]}`."
        )

    @app_commands.command(name="embed", description="Send a custom GVRN embed.")
    @app_commands.describe(
        description="Embed message",
        title="Optional embed title",
        footer="Optional footer",
        colour="Optional hex colour such as 7EC8E3",
    )
    async def embed(
        self,
        interaction: discord.Interaction,
        description: str,
        title: str | None = None,
        footer: str | None = None,
        colour: str | None = None,
    ):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "You need Manage Messages permission.",
                ephemeral=True,
            )
            return

        embed_colour = EMBED_COLOR

        if colour:
            try:
                embed_colour = int(colour.replace("#", "").strip(), 16)
                if not 0 <= embed_colour <= 0xFFFFFF:
                    raise ValueError
            except ValueError:
                await interaction.response.send_message(
                    "Use a valid hex colour, for example `7EC8E3`.",
                    ephemeral=True,
                )
                return

        embed = discord.Embed(
            title=title,
            description=description,
            colour=embed_colour,
        )

        if footer:
            embed.set_footer(text=footer)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Show information about a member.")
    @app_commands.describe(member="Member to inspect")
    async def userinfo(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
    ):
        member = member or interaction.user

        embed = discord.Embed(
            title=f"User Information: {member}",
            colour=EMBED_COLOR,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User ID", value=str(member.id), inline=False)
        embed.add_field(name="Created", value=discord.utils.format_dt(member.created_at, "F"), inline=False)

        if member.joined_at:
            embed.add_field(
                name="Joined Server",
                value=discord.utils.format_dt(member.joined_at, "F"),
                inline=False,
            )

        roles = [role.mention for role in member.roles if role != interaction.guild.default_role]
        embed.add_field(
            name="Roles",
            value=", ".join(roles[-15:]) if roles else "None",
            inline=False,
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Show server information.")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild

        embed = discord.Embed(
            title=guild.name,
            colour=EMBED_COLOR,
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        embed.add_field(name="Server ID", value=str(guild.id), inline=False)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(guild.created_at, "F"), inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ExtraCommands(bot))
