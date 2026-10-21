import json
import os
import re
import time
from pathlib import Path

import discord
from discord.ext import commands
from google import genai

PARTNERSHIP_CHANNEL_ID = 1531721204245856326
AI_MODEL = "gemini-2.5-flash"
AI_COOLDOWN_SECONDS = 45
PARTNER_POSTS_FILE = Path(__file__).with_name("partner_posts.json")

PARTNER_TICKETS = {}
AI_LAST_REPLY = {}

SYSTEM_PROMPT = """
You are GVRN's helpful ticket assistant.
Answer questions about partnerships, joining requirements, applications, tickets, and server help.
Do not use emojis.
Do not invent requirements.
Keep replies short and professional.
"""

TRIGGER_WORDS = (
    "partner",
    "partnership",
    "join",
    "joining",
    "requirement",
    "requirements",
    "application",
)


def is_ticket_channel(channel):
    topic = (getattr(channel, "topic", "") or "").lower()
    name = (getattr(channel, "name", "") or "").lower()
    category = (getattr(getattr(channel, "category", None), "name", "") or "").lower()

    return (
        topic.startswith("ticket-owner:")
        or "ticket" in name
        or "ticket" in category
    )


def load_partner_posts():
    try:
        return set(json.loads(PARTNER_POSTS_FILE.read_text()))
    except Exception:
        return set()


def save_partner_posts(posts):
    PARTNER_POSTS_FILE.write_text(json.dumps(sorted(posts), indent=2))


def get_member_tier(member_count):
    if member_count <= 20:
        return "@here"
    if member_count <= 50:
        return "@everyone"
    return "@everyone"


def get_requirement(member_count):
    if member_count <= 20:
        return "0-20 members: three members from your server must join GVRN."
    if member_count <= 50:
        return "21-50 members: two members from your server must join GVRN."
    return "51+ members: both servers may use an everyone ping."


class AITicketAssistant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        mentioned = self.bot.user is not None and self.bot.user in message.mentions

        if not is_ticket_channel(message.channel) and not mentioned:
            return

        content = (message.content or "").strip()

        if mentioned:
            content = content.replace(self.bot.user.mention, "").strip()

        lowered = content.lower()
        ticket_id = message.channel.id
        user_id = message.author.id

        workflow = PARTNER_TICKETS.get(ticket_id)

        if workflow and workflow["user_id"] != user_id:
            return

        if workflow:
            if workflow["stage"] == "member_count":
                match = re.search(r"\b(\d[\d,]*)\b", content)

                if not match:
                    await message.reply(
                        "Please tell me how many members your server has.",
                        mention_author=False,
                    )
                    return

                member_count = int(match.group(1).replace(",", ""))
                workflow["member_count"] = member_count
                workflow["stage"] = "advertisement"

                await message.reply(
                    f"{get_requirement(member_count)}\n\n"
                    "Please send the partnership advertisement you want posted.",
                    mention_author=False,
                )
                return

            if workflow["stage"] == "advertisement":
                posts = load_partner_posts()
                ticket_key = str(ticket_id)

                if ticket_key in posts:
                    return

                member_count = workflow["member_count"]
                ping = get_member_tier(member_count)
                destination = self.bot.get_channel(PARTNERSHIP_CHANNEL_ID)

                if destination is None:
                    await message.reply(
                        "I could not find the partnership channel. Please contact staff.",
                        mention_author=False,
                    )
                    return

                embed = discord.Embed(
                    title="GVRN Partnership Advertisement",
                    description=content[:4000],
                    color=0xF5935F,
                )
                embed.add_field(
                    name="Server Representative",
                    value=message.author.mention,
                    inline=True,
                )
                embed.add_field(
                    name="Server Members",
                    value=f"{member_count:,}",
                    inline=True,
                )
                embed.set_footer(text="GVRN Partnership Network")

                await destination.send(
                    content=f"{ping} | Representative: {message.author.mention}",
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions(
                        everyone=True,
                        users=True,
                    ),
                )

                posts.add(ticket_key)
                save_partner_posts(posts)
                PARTNER_TICKETS.pop(ticket_id, None)

                await message.reply(
                    "Your partnership advertisement has been sent to the GVRN partners channel.",
                    mention_author=False,
                )
                return

        if (
            "partnership" in lowered
            or "partner" in lowered
        ):
            PARTNER_TICKETS[ticket_id] = {
                "user_id": user_id,
                "stage": "member_count",
            }

            await message.reply(
                "How many members does your server currently have?",
                mention_author=False,
            )
            return

        if not self.client:
            return

        if not any(word in lowered for word in TRIGGER_WORDS):
            return

        now = time.monotonic()
        last_reply = AI_LAST_REPLY.get(ticket_id, 0)

        if now - last_reply < AI_COOLDOWN_SECONDS:
            return

        AI_LAST_REPLY[ticket_id] = now

        prompt = f"{SYSTEM_PROMPT}\n\nTicket question:\n{content}"

        try:
            response = await self.client.aio.models.generate_content(
                model=AI_MODEL,
                contents=prompt,
            )
            answer = (response.text or "").strip()

            if answer:
                await message.reply(answer[:1900], mention_author=False)

        except Exception as error:
            print(f"Gemini ticket assistant error: {error}")


async def setup(bot):
    await bot.add_cog(AITicketAssistant(bot))
