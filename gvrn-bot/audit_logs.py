import os

import discord
from discord.ext import commands


MODLOG_CHANNEL_ID = int(os.getenv("MODLOG_CHANNEL_ID", "0") or 0)
LOG_COLOR = 0x7EC8E3
MESSAGE_CACHE = {}


class AuditLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log(self, title, description):
        channel = self.bot.get_channel(MODLOG_CHANNEL_ID)

        if not isinstance(channel, discord.TextChannel):
            return

        embed = discord.Embed(
            title=title,
            description=description[:4000],
            color=LOG_COLOR,
        )

        await channel.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild and not message.author.bot:
            MESSAGE_CACHE[message.id] = {
                "author": str(message.author),
                "content": message.content or "[No text]",
                "channel": message.channel.mention,
            }

            if len(MESSAGE_CACHE) > 10000:
                MESSAGE_CACHE.pop(next(iter(MESSAGE_CACHE)))

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        cached = MESSAGE_CACHE.pop(payload.message_id, None)

        if not cached:
            return

        await self.log(
            "Message Deleted",
            (
                f"Author: {cached['author']}\n"
                f"Channel: {cached['channel']}\n"
                f"Content:\n{cached['content']}"
            ),
        )

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        cached = MESSAGE_CACHE.get(payload.message_id)

        if not cached:
            return

        new_content = payload.data.get("content")

        if not new_content or new_content == cached["content"]:
            return

        await self.log(
            "Message Edited",
            (
                f"Author: {cached['author']}\n"
                f"Channel: {cached['channel']}\n\n"
                f"Before:\n{cached['content']}\n\n"
                f"After:\n{new_content}"
            ),
        )

        cached["content"] = new_content

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        deleted = []

        for message_id in payload.message_ids:
            cached = MESSAGE_CACHE.pop(message_id, None)
            if cached:
                deleted.append(cached["content"])

        if deleted:
            await self.log(
                "Bulk Messages Deleted",
                f"Channel ID: `{payload.channel_id}`\n"
                f"Messages removed: **{len(deleted)}**\n\n"
                + "\n".join(deleted[:20]),
            )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.log(
            "Channel Created",
            f"Channel: {channel.name}\nID: `{channel.id}`",
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.log(
            "Channel Deleted",
            f"Channel: {channel.name}\nID: `{channel.id}`",
        )

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        changes = []

        if before.name != after.name:
            changes.append(f"Name: `{before.name}` → `{after.name}`")

        if before.category != after.category:
            changes.append("Category changed")

        if changes:
            await self.log(
                "Channel Updated",
                f"Channel: {after.name}\n" + "\n".join(changes),
            )

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self.log(
            "Role Created",
            f"Role: {role.name}\nID: `{role.id}`",
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.log(
            "Role Deleted",
            f"Role: {role.name}\nID: `{role.id}`",
        )

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        changes = []

        if before.name != after.name:
            changes.append(f"Name: `{before.name}` → `{after.name}`")

        if before.colour != after.colour:
            changes.append("Colour changed")

        if before.permissions != after.permissions:
            changes.append("Permissions changed")

        if before.position != after.position:
            changes.append("Position changed")

        if changes:
            await self.log(
                "Role Updated",
                f"Role: {after.name}\n" + "\n".join(changes),
            )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.log(
            "Member Joined",
            f"Member: {member}\nID: `{member.id}`",
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.log(
            "Member Left or Was Removed",
            f"Member: {member}\nID: `{member.id}`",
        )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        changes = []

        if before.nick != after.nick:
            changes.append(
                f"Nickname: `{before.nick}` → `{after.nick}`"
            )

        before_roles = {role.id for role in before.roles}
        after_roles = {role.id for role in after.roles}

        added = after_roles - before_roles
        removed = before_roles - after_roles

        if added:
            changes.append(f"Roles added: `{', '.join(map(str, added))}`")

        if removed:
            changes.append(f"Roles removed: `{', '.join(map(str, removed))}`")

        if changes:
            await self.log(
                "Member Updated",
                f"Member: {after.mention}\n" + "\n".join(changes),
            )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.log(
            "Member Banned",
            f"Member: {user}\nID: `{user.id}`",
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.log(
            "Member Unbanned",
            f"Member: {user}\nID: `{user.id}`",
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return

        old_channel = before.channel.name if before.channel else "None"
        new_channel = after.channel.name if after.channel else "None"

        await self.log(
            "Voice Channel Updated",
            f"Member: {member.mention}\n"
            f"From: `{old_channel}`\n"
            f"To: `{new_channel}`",
        )


async def setup(bot):
    await bot.add_cog(AuditLogs(bot))
