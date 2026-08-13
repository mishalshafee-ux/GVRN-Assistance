import discord

SESSION_CLEANUP_KEYWORDS = [
    "Roleplay Session Startup",
    "Roleplay Session Released",
    "Roleplay Session Reinvites",
    "Session Reinvites",
    "Session Released",
    "Session Setup",
    "Session Conclusion",
    "Link Regeneration",
    "Session Early Access",
]


async def clear_session_embeds(channel: discord.TextChannel, bot_user: discord.ClientUser):
    def should_delete(message: discord.Message):
        if message.author.id != bot_user.id:
            return False

        if not message.embeds:
            return False

        text = ""
        for embed in message.embeds:
            text += str(embed.title or "")
            text += str(embed.description or "")
            text += str(embed.footer.text or "")

        return any(keyword in text for keyword in SESSION_CLEANUP_KEYWORDS)

    await channel.purge(
        limit=100,
        check=should_delete,
        bulk=True,
        reason="Clearing old session messages.",
    )
