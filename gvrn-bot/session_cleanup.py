import discord


async def clear_bot_embeds(channel: discord.TextChannel, bot_user: discord.ClientUser):
    def should_delete(message: discord.Message):
        if message.author.id != bot_user.id:
            return False

        return bool(message.embeds)

    await channel.purge(
        limit=100,
        check=should_delete,
        bulk=True,
        reason="Clearing old bot embed session messages.",
    )
