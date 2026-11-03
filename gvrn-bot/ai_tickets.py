import asyncio
import json
import os
import re
import time
from pathlib import Path
from dotenv import load_dotenv

import discord
from discord.ext import commands
import aiohttp
from ai_control import is_ai_enabled
from ticket_ai_control import is_ticket_ai_enabled

load_dotenv(Path(__file__).resolve().parent.parent / '.env')
load_dotenv()

PARTNERSHIP_CHANNEL_ID = 1531721204245856326
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
AI_COOLDOWN_SECONDS = 3
PARTNER_POSTS_FILE = Path(__file__).with_name("partner_posts.json")

PARTNER_TICKETS = {}
AI_LAST_REPLY = {}
AI_PROCESSED_MESSAGES = set()
AI_INTERACTION_IDS = {}
AI_HISTORY = {}

SYSTEM_PROMPT = """
You are GVRN's ticket assistant.

Identity:
- GVRN means Greenville Roleplay Network.
- You were developed and are operated by Miguel, the owner of GVRN.
- If asked who owns or developed you, say Miguel.
- Do not claim that OpenRouter, Gemini, or another AI provider owns or developed you.

Help with partnerships, applications, appeals, tickets, and general server support.
Do not use emojis.
Do not invent GVRN rules.

Partnership information:
- 0-20 members: the partner server uses no ping and GVRN uses a here ping.
- 21-50 members: the partner server uses a here ping and GVRN uses an everyone ping.
- 51+ members: both servers may use an everyone ping.

These are ping policies only. Do not say that members must join either server.
If you are unsure, explain what information is missing and ask a helpful follow-up question.
Answer clearly and professionally.
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
        return "0-20 members: the partner server uses no ping and GVRN uses a here ping."
    if member_count <= 50:
        return "21-50 members: the partner server uses a here ping and GVRN uses an everyone ping."
    return "51+ members: both servers may use an everyone ping."


def local_ai_fallback(question):
    question = question.lower().strip()

    if any(word in question for word in ("what questions", "what can you answer", "help with")):
        return (
            "I can help with GVRN partnerships, partnership requirements, "
            "advertisement submissions, applications, appeals, reports, "
            "ticket questions, and general server support."
        )

    if "partnership ticket" in question:
        return (
            "Yes, this is a partnership ticket. I can guide you through "
            "the partnership process."
        )

    if any(word in question for word in ("partner", "partnership", "requirement", "criteria")):
        return (
            "**GVRN Partnership Requirements**\n\n"
            "**0-20 members:** Your server uses no ping; GVRN uses a here ping.\n"
            "**21-50 members:** Your server uses a here ping; GVRN uses an everyone ping.\n"
            "**51+ members:** Both servers may use an everyone ping.\n\n"
            "To submit an advertisement, open a partnership ticket."
        )

    if any(word in question for word in ("send my ad", "submit my ad", "advertisement")):
        return "Please open a partnership ticket to submit your advertisement."

    greeting_words = {"hi", "hello", "hey"}
    if question in greeting_words:
        return "Hello."

    if question in {"how are you", "how is life", "hows life", "how's life"}:
        return "I am doing well, thank you."

    return (
        "I can help with GVRN partnerships, applications, appeals, "
        "reports, and general server questions."
    )

class AITicketAssistant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_key = api_key
        print(f"OpenRouter API key configured: {bool(api_key)}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if self.bot.user and message.author.id == self.bot.user.id:
            return

        if message.id in AI_PROCESSED_MESSAGES:
            return

        AI_PROCESSED_MESSAGES.add(message.id)

        if len(AI_PROCESSED_MESSAGES) > 5000:
            AI_PROCESSED_MESSAGES.clear()

        mentioned = False

        if self.bot.user is not None:
            mentioned = (
                self.bot.user in message.mentions
                or f"<@{self.bot.user.id}>" in message.content
                or f"<@!{self.bot.user.id}>" in message.content
            )

        print(
            f"AI event: channel={message.channel.id}, "
            f"mentioned={mentioned}, content={message.content!r}"
        )

        in_ticket = is_ticket_channel(message.channel)
        ticket_ai_enabled = (
            in_ticket and is_ticket_ai_enabled(message.channel.id)
        )

        if not in_ticket and not mentioned:
            return

        content = (message.content or "").strip()

        if mentioned:
            content = content.replace(self.bot.user.mention, "").strip()

        lowered = content.lower()
        ticket_id = message.channel.id
        user_id = message.author.id

        ad_request_words = (
            "send my ad",
            "send an ad",
            "submit my ad",
            "submit an advertisement",
            "post my ad",
            "post an advertisement",
        )

        if any(word in lowered for word in ad_request_words) and not is_ticket_channel(message.channel):
            await message.channel.send(
                "Please open a partnership ticket before submitting an advertisement.",
            )
            return

        workflow = PARTNER_TICKETS.get(ticket_id)

        if workflow and workflow["user_id"] != user_id:
            return

        if workflow:
            if workflow["stage"] == "member_count":
                match = re.search(r"\b(\d[\d,]*)\b", content)

                if not match:
                    await message.channel.send(
                        "Please tell me how many members your server has.",
                            )
                    return

                member_count = int(match.group(1).replace(",", ""))
                workflow["member_count"] = member_count
                workflow["stage"] = "advertisement"

                await message.channel.send(
                    f"{get_requirement(member_count)}\n\n"
                    "Please send the partnership advertisement you want posted.",
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
                    await message.channel.send(
                        "I could not find the partnership channel. Please contact staff.",
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

                await message.channel.send(
                    "Your partnership advertisement has been sent to the GVRN partners channel.",
                    )
                return

        requirement_words = (
            "requirement",
            "requirements",
            "criteria",
            "what do i need",
            "how do i partner",
        )

        advertisement_words = (
            "send my ad",
            "send an ad",
            "submit my ad",
            "submit an advertisement",
            "post my ad",
            "post an advertisement",
        )

        if any(word in lowered for word in requirement_words) and not any(
            word in lowered for word in advertisement_words
        ):
            if is_ticket_channel(message.channel):
                PARTNER_TICKETS[ticket_id] = {
                    "user_id": user_id,
                    "stage": "member_count",
                }

            await message.channel.send(
                "**GVRN Partnership Requirements**\n\n"
                "**0-20 members:** No ping for your server; GVRN uses a here ping.\n"
                "**21-50 members:** Your server uses a here ping; GVRN uses an everyone ping.\n"
                "**51+ members:** Both servers may use an everyone ping.\n\n"
                "Your advertisement must clearly show your server name, invite link, "
                "community type, and partnership information.",
            )
            return

        has_partnership_word = any(
            word in lowered
            for word in ("partner", "partnership", "parnthership")
        )

        has_member_count = bool(re.search(r"\b\d[\d,]*\b", content))

        if (
            any(word in lowered for word in advertisement_words)
            or (
                has_partnership_word
                and has_member_count
                and not any(word in lowered for word in requirement_words)
            )
        ):
            PARTNER_TICKETS[ticket_id] = {
                "user_id": user_id,
                "stage": "member_count",
            }

            await message.channel.send(
                "How many members does your server currently have?",
            )
            return

        ai_enabled = is_ai_enabled(message.guild.id)
        print(f"AI enabled for guild {message.guild.id}: {ai_enabled}")

        if not ai_enabled:
            return

        if not self.api_key:
            await message.channel.send(
                "The AI assistant is not configured yet. Please contact staff.",
            )
            return

        if not mentioned and not ticket_ai_enabled:
            return

        now = time.monotonic()
        last_reply = AI_LAST_REPLY.get(ticket_id, 0)

        if now - last_reply < AI_COOLDOWN_SECONDS:
            return

        AI_LAST_REPLY[ticket_id] = now

        prompt = f"{SYSTEM_PROMPT}\n\nTicket question:\n{content}"

        try:
            print("OpenRouter request started.")

            payload = {
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *AI_HISTORY.get(ticket_id, [])[-10:],
                    {"role": "user", "content": content},
                ],
            }

            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://gvrn.wispbyte.app",
                        "X-Title": "GVRN Discord Assistant",
                    },
                    json=payload,
                ) as response:
                    data = await response.json(content_type=None)

                    if response.status >= 400:
                        raise RuntimeError(
                            f"OpenRouter HTTP {response.status}: {data}"
                        )

            message_data = data.get("choices", [{}])[0].get("message", {})
            answer = message_data.get("content", "")

            if isinstance(answer, list):
                answer = "".join(
                    part.get("text", "")
                    for part in answer
                    if isinstance(part, dict)
                )

            if not answer:
                answer = message_data.get("reasoning", "")

            answer = str(answer).strip()

            print(
                "OpenRouter response received. "
                f"Characters: {len(answer)}"
            )

            if not answer:
                print(f"OpenRouter returned no text. Keys: {list(data.keys())}")
                await message.channel.send(
                    "I received an empty AI response. Please try again."
                )
                return

            AI_HISTORY.setdefault(ticket_id, []).append(
                {"role": "user", "content": content}
            )
            AI_HISTORY[ticket_id].append(
                {"role": "assistant", "content": answer}
            )
            AI_HISTORY[ticket_id] = AI_HISTORY[ticket_id][-10:]

            await message.channel.send(answer[:1900])

        except Exception as error:
            print(
                "OpenRouter ticket assistant error: "
                f"{type(error).__name__}: {error!r}"
            )
            await message.channel.send(
                "OpenRouter is temporarily unavailable. Please try again in a moment."
            )


async def setup(bot):
    await bot.add_cog(AITicketAssistant(bot))
