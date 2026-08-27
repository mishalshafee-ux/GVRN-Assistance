import discord

SESSION_DELETE_FOOTERS = {
    "GVRN Sessions",
    "GVRN Early Access",
    "GVRN Session Released",
    "GVRN Re-Invites",
    "GVRN Session Concluded",
    "GVRN Link Regeneration",
}

SESSION_KEEP_FOOTERS = {
    "GVRN Session Information",
    "Greenville Roleplay Network",
}


def get_footer(message):
    if not message.embeds:
        return ""

    footer = message.embeds[0].footer
    return footer.text if footer and footer.text else ""


def should_delete_session_message(message):
    if not message.author.bot:
        return False

    footer = get_footer(message)

    if footer in SESSION_KEEP_FOOTERS:
        return False

    if footer in SESSION_DELETE_FOOTERS:
        return True

    return False


async def clear_session_messages(channel):
    deleted = 0

    async for message in channel.history(limit=75):
        if should_delete_session_message(message):
            try:
                await message.delete()
                deleted += 1
            except discord.HTTPException:
                pass

    return deleted


async def clear_session_embeds(channel):
    return await clear_session_messages(channel)


async def clear_old_session_messages(channel):
    return await clear_session_messages(channel)


async def cleanup_session_messages(channel):
    return await clear_session_messages(channel)
