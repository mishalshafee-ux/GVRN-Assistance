import os

import discord
from discord.ext import commands

MARKETPLACE_TICKET_CATEGORY_ID = int(os.getenv("MARKETPLACE_TICKET_CATEGORY_ID", "0"))
GENERAL_TICKET_CATEGORY_ID = int(os.getenv("GENERAL_TICKET_CATEGORY_ID", "0"))
REPORT_TICKET_CATEGORY_ID = int(os.getenv("REPORT_TICKET_CATEGORY_ID", "0"))

MARKETPLACE_STAFF_ROLE_ID = int(os.getenv("MARKETPLACE_STAFF_ROLE_ID", "0"))
GENERAL_STAFF_ROLE_ID = int(os.getenv("GENERAL_STAFF_ROLE_ID", "0"))
REPORT_STAFF_ROLE_ID = int(os.getenv("REPORT_STAFF_ROLE_ID", "0"))
MAX_OPEN_TICKETS_PER_USER = int(os.getenv("MAX_OPEN_TICKETS_PER_USER", "1"))

# =========================
# PANEL TEXT EDIT AREA
# =========================

SERVER_NAME = "GVRN"
PANEL_TITLE = "GVRN Support Centre"
PANEL_BANNER_URL = ""
PANEL_COLOR = 0x76F55D

PANEL_DESCRIPTION = (
    "If you have questions, encounter a bug, or need assistance, "
    "our support team is here for you. Open a ticket and we will respond as quickly as possible."
)

MARKETPLACE_PANEL_NAME = "Marketplace Support"
MARKETPLACE_PANEL_TEXT = (
    "For marketplace listings, paid services, items, or payment questions.\n\n"
    "~ Paid ads\n"
    "~ Sponsored giveaways\n"
    "~ Payment questions\n"
    "~ Marketplace listings"
)

GENERAL_PANEL_NAME = "General Support"
GENERAL_PANEL_TEXT = (
    "For general questions, help, concerns, or server support.\n\n"
    "~ General questions\n"
    "~ Server help\n"
    "~ Partnership questions\n"
    "~ Other concerns"
)

REPORT_PANEL_NAME = "Report Support"
REPORT_PANEL_TEXT = (
    "For reporting players, staff, rule violations, or safety concerns.\n\n"
    "~ Player report\n"
    "~ Staff report\n"
    "~ Rule violation\n"
    "~ Safety concern"
)

# =========================
# END PANEL TEXT EDIT AREA
# =========================

TICKET_TYPES = {
    "marketplace": {
        "label": MARKETPLACE_PANEL_NAME,
        "emoji": "🛒",
        "button_style": discord.ButtonStyle.primary,
        "channel_prefix": "marketplace",
        "category_id": MARKETPLACE_TICKET_CATEGORY_ID,
        "staff_role_id": MARKETPLACE_STAFF_ROLE_ID,
        "panel_text": MARKETPLACE_PANEL_TEXT,
    },
    "general": {
        "label": GENERAL_PANEL_NAME,
        "emoji": "📋",
        "button_style": discord.ButtonStyle.success,
        "channel_prefix": "general",
        "category_id": GENERAL_TICKET_CATEGORY_ID,
        "staff_role_id": GENERAL_STAFF_ROLE_ID,
        "panel_text": GENERAL_PANEL_TEXT,
    },
    "report": {
        "label": REPORT_PANEL_NAME,
        "emoji": "🚨",
        "button_style": discord.ButtonStyle.danger,
        "channel_prefix": "report",
        "category_id": REPORT_TICKET_CATEGORY_ID,
        "staff_role_id": REPORT_STAFF_ROLE_ID,
        "panel_text": REPORT_PANEL_TEXT,
    },
}


def build_panel_embed():
    embed = discord.Embed(
        title=PANEL_TITLE,
        description=PANEL_DESCRIPTION,
        color=PANEL_COLOR,
    )

    if PANEL_BANNER_URL:
        embed.set_image(url=PANEL_BANNER_URL)

    for ticket in TICKET_TYPES.values():
        embed.add_field(
            name=ticket["label"],
            value=ticket["panel_text"],
            inline=False,
        )

    embed.set_footer(text=f"{SERVER_NAME} Tickets")
    return embed


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket_button",
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Closing ticket...", ephemeral=True)
        await interaction.channel.delete(reason=f"Closed by {interaction.user}")


class TicketButton(discord.ui.Button):
    def __init__(self, ticket_key, ticket):
        super().__init__(
            label=ticket["label"],
            emoji=ticket["emoji"],
            style=ticket["button_style"],
            custom_id=f"ticket_button_{ticket_key}",
        )
        self.ticket_key = ticket_key

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        if guild is None or not isinstance(user, discord.Member):
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        ticket = TICKET_TYPES[self.ticket_key]
        category = guild.get_channel(ticket["category_id"])

        if not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message(
                "Ticket category not found. Check the category ID in .env.",
                ephemeral=True,
            )
            return

        open_tickets = [
            channel
            for ticket_type in TICKET_TYPES.values()
            for ticket_category in [guild.get_channel(ticket_type["category_id"])]
            if isinstance(ticket_category, discord.CategoryChannel)
            for channel in ticket_category.text_channels
            if channel.topic == f"ticket-owner:{user.id}"
        ]

        if len(open_tickets) >= MAX_OPEN_TICKETS_PER_USER:
            ticket_mentions = ", ".join(channel.mention for channel in open_tickets[:3])
            await interaction.response.send_message(
                f"You already have the maximum allowed open ticket(s): {ticket_mentions}",
                ephemeral=True,
            )
            return

        staff_role = guild.get_role(ticket["staff_role_id"])

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
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

        username = user.name.lower().replace(" ", "-")[:20]
        channel_name = f"{ticket['channel_prefix']}-{username}"

        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"ticket-owner:{user.id}",
            reason=f"Ticket opened by {user}",
        )

        embed = discord.Embed(
            title=ticket["label"],
            description=(
                f"Hello {user.mention}, thank you for opening a ticket.\n"
                f"The needed staff team has been pinged.\n\n"
                f"{ticket['panel_text']}"
            ),
            color=PANEL_COLOR,
        )
        embed.set_footer(text=f"{SERVER_NAME} Support")

        ping_message = user.mention

        if staff_role:
            ping_message += f" {staff_role.mention}"

        await channel.send(
            ping_message,
            embed=embed,
            view=CloseTicketView(),
        )

        await interaction.response.send_message(
            f"Your ticket has been created: {channel.mention}",
            ephemeral=True,
        )


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        for ticket_key, ticket in TICKET_TYPES.items():
            self.add_item(TicketButton(ticket_key, ticket))


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(TicketPanelView())
        bot.add_view(CloseTicketView())

    @commands.command(name="ticketpanel")
    @commands.has_permissions(administrator=True)
    async def ticketpanel(self, ctx):
        await ctx.send(embed=build_panel_embed(), view=TicketPanelView())


async def setup(bot):
    await bot.add_cog(Tickets(bot))
