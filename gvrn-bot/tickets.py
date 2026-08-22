import io
import os
from datetime import datetime, timezone

import discord
from discord.ext import commands

COLOR = 0x76F55D

MAX_OPEN_TICKETS_PER_USER = int(os.getenv("MAX_OPEN_TICKETS_PER_USER", "1"))
TICKET_TRANSCRIPT_LOG_CHANNEL_ID = int(os.getenv("TICKET_TRANSCRIPT_LOG_CHANNEL_ID", "0"))
TICKET_RATING_LOG_CHANNEL_ID = int(os.getenv("TICKET_RATING_LOG_CHANNEL_ID", "0"))
STAFF_ACTIVITY_LOG_CHANNEL_ID = int(os.getenv("STAFF_ACTIVITY_LOG_CHANNEL_ID", "0"))

TICKET_TYPES = {
    "marketplace": {
        "label": "Marketplace Support",
        "emoji": "🛒",
        "category_id": int(os.getenv("MARKETPLACE_TICKET_CATEGORY_ID", "0")),
        "staff_role_id": int(os.getenv("MARKETPLACE_STAFF_ROLE_ID", "0")),
        "prefix": "marketplace",
        "description": "For marketplace listings, paid services, items, or payment questions.",
        "details": ["Paid ads", "Sponsored giveaways", "Payment questions", "Marketplace listings"],
        "questions": [
            "What are you needing help with?",
            "Is this about paid ads, sponsored giveaways, payments, or listings?",
            "Please provide any proof, screenshots, or links if needed.",
        ],
    },
    "general": {
        "label": "General Support",
        "emoji": "📋",
        "category_id": int(os.getenv("GENERAL_TICKET_CATEGORY_ID", "0")),
        "staff_role_id": int(os.getenv("GENERAL_STAFF_ROLE_ID", "0")),
        "prefix": "general",
        "description": "For general questions, help, concerns, or server support.",
        "details": ["General questions", "Server help", "Partnership questions", "Other concerns"],
        "questions": [
            "What do you need help with?",
            "Please explain your issue clearly.",
            "Is there anyone specific staff should contact about this?",
        ],
    },
    "report": {
        "label": "Report Support",
        "emoji": "🚨",
        "category_id": int(os.getenv("REPORT_TICKET_CATEGORY_ID", "0")),
        "staff_role_id": int(os.getenv("REPORT_STAFF_ROLE_ID", "0")),
        "prefix": "report",
        "description": "For reporting players, staff, rule violations, or safety concerns.",
        "details": ["Player report", "Staff report", "Rule violation", "Safety concern"],
        "questions": [
            "Who are you reporting?",
            "What rule was broken?",
            "When did this happen?",
            "Please send screenshots, clips, or proof.",
        ],
    },
}


def parse_topic(topic):
    data = {}
    if not topic:
        return data

    for part in topic.split("|"):
        if ":" in part:
            key, value = part.strip().split(":", 1)
            data[key.strip()] = value.strip()

    return data


def make_topic(owner_id, ticket_type, claimed_by=0):
    return f"ticket-owner:{owner_id}|ticket-type:{ticket_type}|claimed-by:{claimed_by}"


def has_staff_access(member, staff_role_id):
    if member.guild_permissions.manage_channels:
        return True

    return any(role.id == staff_role_id for role in member.roles)


async def log_staff_activity(guild, text):
    channel = guild.get_channel(STAFF_ACTIVITY_LOG_CHANNEL_ID)
    if isinstance(channel, discord.TextChannel):
        await channel.send(text, allowed_mentions=discord.AllowedMentions.none())


async def make_transcript(channel):
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
            attachments = " ".join(attachment.url for attachment in message.attachments)
            content = f"{content} [Attachments: {attachments}]".strip()

        if message.embeds:
            content = f"{content} [Embed sent]".strip()

        lines.append(f"[{created}] {message.author}: {content}")

    filename = f"{channel.name}-transcript.txt"
    transcript_data = "\n".join(lines).encode("utf-8")
    return filename, transcript_data


def transcript_file(filename, transcript_data):
    return discord.File(fp=io.BytesIO(transcript_data), filename=filename)


def ticket_embed(user, config):
    details = "\n".join(f"~ {item}" for item in config["details"])
    questions = "\n".join(f"**{index}.** {question}" for index, question in enumerate(config["questions"], start=1))

    embed = discord.Embed(
        title=config["label"],
        description=(
            f"Hello {user.mention}, thank you for opening a ticket.\n"
            f"The needed staff team has been pinged.\n\n"
            f"{config['description']}\n\n"
            f"{details}\n\n"
            f"**Please answer these questions:**\n"
            f"{questions}"
        ),
        color=COLOR,
    )
    embed.set_footer(text="GVRN Support")
    return embed


class TicketRatingView(discord.ui.View):
    def __init__(self, ticket_name, opener_id, closed_by_id):
        super().__init__(timeout=None)
        for rating in range(1, 6):
            self.add_item(TicketRatingButton(rating, ticket_name, opener_id, closed_by_id))


class TicketRatingButton(discord.ui.Button):
    def __init__(self, rating, ticket_name, opener_id, closed_by_id):
        super().__init__(
            label=f"{rating} ⭐",
            style=discord.ButtonStyle.secondary,
            custom_id=f"ticket_rating:{rating}:{opener_id}",
        )
        self.rating = rating
        self.ticket_name = ticket_name
        self.opener_id = opener_id
        self.closed_by_id = closed_by_id

    async def callback(self, interaction):
        if interaction.user.id != self.opener_id:
            await interaction.response.send_message("Only the ticket opener can rate this ticket.", ephemeral=True)
            return

        guild = interaction.client.get_guild(int(os.getenv("GUILD_ID", "0")))
        if guild:
            channel = guild.get_channel(TICKET_RATING_LOG_CHANNEL_ID)
            if isinstance(channel, discord.TextChannel):
                await channel.send(
                    f"⭐ **Ticket Rating:** {self.rating}/5\n"
                    f"Ticket: `{self.ticket_name}`\n"
                    f"Rated by: {interaction.user.mention}\n"
                    f"Closed by: <@{self.closed_by_id}>",
                    allowed_mentions=discord.AllowedMentions(users=True),
                )

        for item in self.view.children:
            item.disabled = True

        await interaction.response.edit_message(
            content=f"Thanks for rating your ticket **{self.rating}/5** ⭐",
            view=self.view,
        )


class TicketControls(discord.ui.View):
    def __init__(self, ticket_type, claimed_by=0):
        super().__init__(timeout=None)

        if claimed_by:
            self.add_item(UnclaimButton(ticket_type))
        else:
            self.add_item(ClaimButton(ticket_type))

        self.add_item(CloseTicketButton(ticket_type))


class ClaimButton(discord.ui.Button):
    def __init__(self, ticket_type):
        super().__init__(label="Claim", style=discord.ButtonStyle.success, custom_id=f"ticket_claim:{ticket_type}")
        self.ticket_type = ticket_type

    async def callback(self, interaction):
        config = TICKET_TYPES[self.ticket_type]

        if not has_staff_access(interaction.user, config["staff_role_id"]):
            await interaction.response.send_message("Only ticket staff can claim this ticket.", ephemeral=True)
            return

        data = parse_topic(interaction.channel.topic)
        owner_id = int(data.get("ticket-owner", "0"))

        await interaction.channel.edit(topic=make_topic(owner_id, self.ticket_type, interaction.user.id))
        await interaction.response.edit_message(view=TicketControls(self.ticket_type, interaction.user.id))
        await interaction.channel.send(f"✅ This ticket has been claimed by {interaction.user.mention}.")
        await log_staff_activity(interaction.guild, f"✅ **Ticket Claimed** | `{interaction.channel.name}` by {interaction.user}.")


class UnclaimButton(discord.ui.Button):
    def __init__(self, ticket_type):
        super().__init__(label="Unclaim", style=discord.ButtonStyle.secondary, custom_id=f"ticket_unclaim:{ticket_type}")
        self.ticket_type = ticket_type

    async def callback(self, interaction):
        config = TICKET_TYPES[self.ticket_type]

        if not has_staff_access(interaction.user, config["staff_role_id"]):
            await interaction.response.send_message("Only ticket staff can unclaim this ticket.", ephemeral=True)
            return

        data = parse_topic(interaction.channel.topic)
        owner_id = int(data.get("ticket-owner", "0"))

        await interaction.channel.edit(topic=make_topic(owner_id, self.ticket_type, 0))
        await interaction.response.edit_message(view=TicketControls(self.ticket_type, 0))
        await interaction.channel.send(f"↩️ This ticket has been unclaimed by {interaction.user.mention}.")
        await log_staff_activity(interaction.guild, f"↩️ **Ticket Unclaimed** | `{interaction.channel.name}` by {interaction.user}.")


class CloseTicketButton(discord.ui.Button):
    def __init__(self, ticket_type):
        super().__init__(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id=f"ticket_close:{ticket_type}")
        self.ticket_type = ticket_type

    async def callback(self, interaction):
        config = TICKET_TYPES[self.ticket_type]

        if not has_staff_access(interaction.user, config["staff_role_id"]):
            await interaction.response.send_message("Only ticket staff can close this ticket.", ephemeral=True)
            return

        await interaction.response.send_message("Closing ticket and sending transcript...", ephemeral=True)

        data = parse_topic(interaction.channel.topic)
        owner_id = int(data.get("ticket-owner", "0"))
        opener = interaction.guild.get_member(owner_id)
        ticket_name = interaction.channel.name

        filename, transcript_data = await make_transcript(interaction.channel)

        if opener:
            try:
                await opener.send(
                    content=f"Here is your ticket transcript from **{interaction.guild.name}**.",
                    file=transcript_file(filename, transcript_data),
                )
                await opener.send(
                    content="How would you rate the support you received?",
                    view=TicketRatingView(ticket_name, opener.id, interaction.user.id),
                )
            except discord.Forbidden:
                await interaction.followup.send("Could not DM the ticket opener.", ephemeral=True)

        log_channel = interaction.guild.get_channel(TICKET_TRANSCRIPT_LOG_CHANNEL_ID)
        if isinstance(log_channel, discord.TextChannel):
            await log_channel.send(
                content=(
                    f"Ticket transcript: **#{ticket_name}**\n"
                    f"Opened by: <@{owner_id}>\n"
                    f"Closed by: {interaction.user.mention}"
                ),
                file=transcript_file(filename, transcript_data),
                allowed_mentions=discord.AllowedMentions(users=True),
            )

        await log_staff_activity(interaction.guild, f"🔒 **Ticket Closed** | `{ticket_name}` by {interaction.user}.")
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

        super().__init__(placeholder="Select a support type...", options=options, custom_id="ticket_type_select")

    async def callback(self, interaction):
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
            await interaction.response.send_message(f"You already have the maximum open ticket(s): {mentions}", ephemeral=True)
            return

        category = guild.get_channel(config["category_id"])
        staff_role = guild.get_role(config["staff_role_id"])

        if not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("Ticket category is not set correctly.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, read_message_history=True),
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True)

        channel = await guild.create_text_channel(
            name=f"{config['prefix']}-{user.name}".lower()[:90],
            category=category,
            overwrites=overwrites,
            topic=make_topic(user.id, ticket_type, 0),
            reason=f"Ticket opened by {user}.",
        )

        staff_ping = staff_role.mention if staff_role else ""

        await channel.send(
            content=f"{user.mention} {staff_ping}",
            embed=ticket_embed(user, config),
            view=TicketControls(ticket_type, 0),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )

        await log_staff_activity(guild, f"🎟️ **Ticket Opened** | `{channel.name}` by {user} | Type: `{config['label']}`.")
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
            self.bot.add_view(TicketControls(ticket_type, 1))

    @commands.command(name="ticketpanel")
    @commands.has_permissions(manage_channels=True)
    async def ticket_panel(self, ctx):
        embed = discord.Embed(
            title="GVRN Support Centre",
            description=(
                "If you have questions, encounter a bug, or need assistance, our support team is here for you. "
                "Open a ticket and we will respond as quickly as possible.\n\n"
                "**Marketplace Support**\n"
                "For marketplace listings, paid services, items, or payment questions.\n\n"
                "~ Paid ads\n~ Sponsored giveaways\n~ Payment questions\n~ Marketplace listings\n\n"
                "**General Support**\n"
                "For general questions, help, concerns, or server support.\n\n"
                "~ General questions\n~ Server help\n~ Partnership questions\n~ Other concerns\n\n"
                "**Report Support**\n"
                "For reporting players, staff, rule violations, or safety concerns.\n\n"
                "~ Player report\n~ Staff report\n~ Rule violation\n~ Safety concern"
            ),
            color=COLOR,
        )
        embed.set_footer(text="GVRN Tickets")
        await ctx.send(embed=embed, view=TicketPanelView())


async def setup(bot):
    await bot.add_cog(Tickets(bot))
