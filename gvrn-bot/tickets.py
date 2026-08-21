import io
import os
from datetime import datetime, timezone

import discord
from discord.ext import commands

COLOR = 0x76F55D
MAX_OPEN_TICKETS_PER_USER = int(os.getenv("MAX_OPEN_TICKETS_PER_USER", "1"))

TICKET_TYPES = {
    "marketplace": {
        "label": "Marketplace",
        "emoji": "🛒",
        "category_id": int(os.getenv("MARKETPLACE_TICKET_CATEGORY_ID", "0")),
        "staff_role_id": int(os.getenv("MARKETPLACE_STAFF_ROLE_ID", "0")),
        "prefix": "marketplace",
        "description": "Marketplace listings, paid services, items, or payment questions.",
    },
    "general": {
        "label": "General",
        "emoji": "❔",
        "category_id": int(os.getenv("GENERAL_TICKET_CATEGORY_ID", "0")),
        "staff_role_id": int(os.getenv("GENERAL_STAFF_ROLE_ID", "0")),
        "prefix": "general",
        "description": "General questions, support, partnerships, or other concerns.",
    },
    "report": {
        "label": "Report",
        "emoji": "🚨",
        "category_id": int(os.getenv("REPORT_TICKET_CATEGORY_ID", "0")),
        "staff_role_id": int(os.getenv("REPORT_STAFF_ROLE_ID", "0")),
        "prefix": "report",
        "description": "Player reports, staff reports, rule violations, or safety concerns.",
    },
}


def parse_topic(topic: str | None):
    data = {}
    if not topic:
        return data

    for part in topic.split("|"):
        if ":" in part:
            key, value = part.strip().split(":", 1)
            data[key.strip()] = value.strip()
    return data


def make_topic(owner_id: int, ticket_type: str, claimed_by: int = 0):
    return f"ticket-owner:{owner_id}|ticket-type:{ticket_type}|claimed-by:{claimed_by}"


def has_staff_access(member: discord.Member, staff_role_id: int):
    if member.guild_permissions.manage_channels:
        return True
    return any(role.id == staff_role_id for role in member.roles)


async def make_transcript(channel: discord.TextChannel):
    lines = [
        f"Transcript for #{channel.name}",
        f"Channel ID: {channel.id}",
        f"Created: {datetime.now(timezone.utc).isoformat()}",
        "-" * 50,
    ]

    async for message in channel.history(limit=None, oldest_first=True):
        created = message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        content = message.content or ""

        if message.attachments:
            attachments = " ".join(a.url for a in message.attachments)
            content = f"{content} [Attachments: {attachments}]".strip()

        if message.embeds:
            content = f"{content} [Embed sent]".strip()

        lines.append(f"[{created}] {message.author}: {content}")

    transcript = "\n".join(lines)
    return discord.File(
        fp=io.BytesIO(transcript.encode("utf-8")),
        filename=f"{channel.name}-transcript.txt",
    )


class TicketControls(discord.ui.View):
    def __init__(self, ticket_type: str, claimed_by: int = 0):
        super().__init__(timeout=None)
        self.ticket_type = ticket_type
        self.claimed_by = claimed_by

        if claimed_by:
            self.add_item(UnclaimButton(ticket_type))
        else:
            self.add_item(ClaimButton(ticket_type))

        self.add_item(CloseTicketButton(ticket_type))


class ClaimButton(discord.ui.Button):
    def __init__(self, ticket_type: str):
        super().__init__(
            label="Claim",
            style=discord.ButtonStyle.success,
            custom_id=f"ticket_claim:{ticket_type}",
        )
        self.ticket_type = ticket_type

    async def callback(self, interaction: discord.Interaction):
        config = TICKET_TYPES[self.ticket_type]

        if not has_staff_access(interaction.user, config["staff_role_id"]):
            await interaction.response.send_message("Only ticket staff can claim this ticket.", ephemeral=True)
            return

        data = parse_topic(interaction.channel.topic)
        owner_id = int(data.get("ticket-owner", "0"))

        await interaction.channel.edit(
            topic=make_topic(owner_id, self.ticket_type, interaction.user.id),
            reason="Ticket claimed.",
        )

        await interaction.response.edit_message(view=TicketControls(self.ticket_type, interaction.user.id))
        await interaction.channel.send(f"✅ This ticket has been claimed by {interaction.user.mention}.")


class UnclaimButton(discord.ui.Button):
    def __init__(self, ticket_type: str):
        super().__init__(
            label="Unclaim",
            style=discord.ButtonStyle.secondary,
            custom_id=f"ticket_unclaim:{ticket_type}",
        )
        self.ticket_type = ticket_type

    async def callback(self, interaction: discord.Interaction):
        config = TICKET_TYPES[self.ticket_type]

        if not has_staff_access(interaction.user, config["staff_role_id"]):
            await interaction.response.send_message("Only ticket staff can unclaim this ticket.", ephemeral=True)
            return

        data = parse_topic(interaction.channel.topic)
        owner_id = int(data.get("ticket-owner", "0"))

        await interaction.channel.edit(
            topic=make_topic(owner_id, self.ticket_type, 0),
            reason="Ticket unclaimed.",
        )

        await interaction.response.edit_message(view=TicketControls(self.ticket_type, 0))
        await interaction.channel.send(f"↩️ This ticket has been unclaimed by {interaction.user.mention}.")


class CloseTicketButton(discord.ui.Button):
    def __init__(self, ticket_type: str):
        super().__init__(
            label="Close Ticket",
            style=discord.ButtonStyle.danger,
            custom_id=f"ticket_close:{ticket_type}",
        )
        self.ticket_type = ticket_type

    async def callback(self, interaction: discord.Interaction):
        config = TICKET_TYPES[self.ticket_type]

        if not has_staff_access(interaction.user, config["staff_role_id"]):
            await interaction.response.send_message("Only ticket staff can close this ticket.", ephemeral=True)
            return

        await interaction.response.send_message("Closing ticket and sending transcript...", ephemeral=True)

        data = parse_topic(interaction.channel.topic)
        owner_id = int(data.get("ticket-owner", "0"))
        opener = interaction.guild.get_member(owner_id)

        transcript = await make_transcript(interaction.channel)

        if opener:
            try:
                await opener.send(
                    content=f"Here is your ticket transcript from **{interaction.guild.name}**.",
                    file=transcript,
                )
            except discord.Forbidden:
                await interaction.followup.send(
                    "I could not DM the ticket opener. Their DMs may be closed.",
                    ephemeral=True,
                )

        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}.")


class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=config["label"],
                value=key,
                emoji=config["emoji"],
                description=config["description"][:100],
            )
            for key, config in TICKET_TYPES.items()
        ]

        super().__init__(
            placeholder="Select a support type...",
            options=options,
            custom_id="ticket_type_select",
        )

    async def callback(self, interaction: discord.Interaction):
        ticket_type = self.values[0]
        config = TICKET_TYPES[ticket_type]
        guild = interaction.guild
        user = interaction.user

        open_tickets = []
        for item in TICKET_TYPES.values():
            category = guild.get_channel(item["category_id"])
            if isinstance(category, discord.CategoryChannel):
                for channel in category.text_channels:
                    data = parse_topic(channel.topic)
                    if data.get("ticket-owner") == str(user.id):
                        open_tickets.append(channel)

        if len(open_tickets) >= MAX_OPEN_TICKETS_PER_USER:
            mentions = ", ".join(channel.mention for channel in open_tickets[:3])
            await interaction.response.send_message(
                f"You already have the maximum open ticket(s): {mentions}",
                ephemeral=True,
            )
            return

        category = guild.get_channel(config["category_id"])
        staff_role = guild.get_role(config["staff_role_id"])

        if not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("Ticket category is not set correctly.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                read_message_history=True,
            ),
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            )

        channel = await guild.create_text_channel(
            name=f"{config['prefix']}-{user.name}".lower()[:90],
            category=category,
            overwrites=overwrites,
            topic=make_topic(user.id, ticket_type, 0),
            reason=f"Ticket opened by {user}.",
        )

        embed = discord.Embed(
            title=f"{config['emoji']} {config['label']} Ticket",
            description=(
                f"Hello {user.mention}, staff will help you shortly.\n\n"
                f"**Reason:** {config['description']}"
            ),
            color=COLOR,
        )

        ping = staff_role.mention if staff_role else "@staff"
        await channel.send(
            content=f"{user.mention} {ping}",
            embed=embed,
            view=TicketControls(ticket_type, 0),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )

        await interaction.response.send_message(f"Created your ticket: {channel.mention}", ephemeral=True)


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(TicketPanelView())

        for ticket_type in TICKET_TYPES:
            self.bot.add_view(TicketControls(ticket_type, 0))

    @commands.command(name="ticketpanel")
    @commands.has_permissions(manage_channels=True)
    async def ticket_panel(self, ctx):
        embed = discord.Embed(
            title="GVRN Support Centre",
            description=(
                "If you need assistance, open a ticket and our team will help you.\n\n"
                "**Marketplace**\nMarketplace listings, paid services, items, or payments.\n\n"
                "**General**\nGeneral questions, partnerships, or other concerns.\n\n"
                "**Report**\nPlayer reports, staff reports, rule violations, or safety concerns."
            ),
            color=COLOR,
        )

        await ctx.send(embed=embed, view=TicketPanelView())


async def setup(bot):
    await bot.add_cog(Tickets(bot))
