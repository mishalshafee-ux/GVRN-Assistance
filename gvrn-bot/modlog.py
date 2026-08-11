import json
import os
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.ext import commands

MODLOG_CHANNEL_ID = int(os.getenv("MODLOG_CHANNEL_ID", "0"))
HIGH_COMMAND_ROLE_ID = int(os.getenv("HIGH_COMMAND_ROLE_ID", "0"))

LOG_FILE = Path("command_logs.json")


def load_logs():
    if not LOG_FILE.exists():
        return []

    with LOG_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_logs(logs):
    with LOG_FILE.open("w", encoding="utf-8") as file:
        json.dump(logs, file, indent=2)


def can_use_role_command(member):
    if member.guild_permissions.administrator:
        return True

    return any(role.id == HIGH_COMMAND_ROLE_ID for role in member.roles)


async def resolve_member(ctx, user_text):
    user_id = user_text.strip()

    if user_id.startswith("<@") and user_id.endswith(">"):
        user_id = user_id.replace("<@", "").replace("!", "").replace(">", "")

    if not user_id.isdigit():
        return None

    member = ctx.guild.get_member(int(user_id))
    if member:
        return member

    try:
        return await ctx.guild.fetch_member(int(user_id))
    except discord.HTTPException:
        return None


async def add_log(bot, guild, channel, user, command_name, details):
    logs = load_logs()

    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "guild": guild.name if guild else "DM",
        "channel": channel.name if hasattr(channel, "name") else "Unknown",
        "user": str(user),
        "user_id": user.id,
        "command": command_name,
        "details": details,
    }

    logs.append(entry)
    save_logs(logs[-500:])

    if guild:
        log_channel = guild.get_channel(MODLOG_CHANNEL_ID)
        if isinstance(log_channel, discord.TextChannel):
            embed = discord.Embed(title="Command Log", color=0x76F55D)
            embed.add_field(name="User", value=user.mention, inline=True)
            embed.add_field(name="Command", value=command_name, inline=True)
            embed.add_field(name="Channel", value=channel.mention if hasattr(channel, "mention") else "Unknown", inline=False)
            embed.add_field(name="Details", value=details[:1000] or "No details.", inline=False)
            await log_channel.send(embed=embed)


class ModLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="role")
    async def role(self, ctx, user_text: str, roles: commands.Greedy[discord.Role], *, reason: str = "No reason provided."):
        if not can_use_role_command(ctx.author):
            await ctx.send("You need High Command+ to use this command.")
            return

        member = await resolve_member(ctx, user_text)

        if member is None:
            await ctx.send("Could not find that user. Use a mention or user ID.")
            return

        if not roles:
            await ctx.send("Mention at least one role. Example: `!role @user @Role reason`")
            return

        added = []
        failed = []

        for role in roles:
            try:
                await member.add_roles(role, reason=f"{reason} | Given by {ctx.author}")
                added.append(role.mention)
            except discord.Forbidden:
                failed.append(role.mention)

        message = f"Added roles to {member.mention}: {', '.join(added) if added else 'None'}"
        if failed:
            message += f"\nCould not add: {', '.join(failed)}"

        await ctx.send(message)

        await add_log(
            self.bot,
            ctx.guild,
            ctx.channel,
            ctx.author,
            "!role",
            f"Target: {member} ({member.id})\nRoles: {', '.join(role.name for role in roles)}\nReason: {reason}",
        )

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

    @commands.command(name="modlog")
    async def modlog(self, ctx, user_text: str = None):
        if not can_use_role_command(ctx.author):
            await ctx.send("You need High Command+ to use this command.")
            return

        logs = load_logs()

        if user_text:
            member = await resolve_member(ctx, user_text)
            if member is None:
                await ctx.send("Could not find that user. Use a mention or user ID.")
                return

            logs = [log for log in logs if str(log.get("user_id")) == str(member.id)]

        if not logs:
            await ctx.send("No logs found.")
            return

        lines = []
        for log in logs:
            lines.append(
                f"[{log['time']}] {log['user']} used {log['command']} in #{log['channel']} | {log['details']}"
            )

        transcript = "\n".join(lines)
        file = discord.File(
            fp=__import__("io").StringIO(transcript),
            filename="modlog.txt",
        )

        await ctx.send("Here are the command logs:", file=file)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.command and ctx.command.name in ["role", "modlog"]:
            return

        await add_log(
            self.bot,
            ctx.guild,
            ctx.channel,
            ctx.author,
            f"!{ctx.command.qualified_name}",
            ctx.message.content,
        )

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type != discord.InteractionType.application_command:
            return

        command_name = interaction.command.name if interaction.command else "unknown"

        await add_log(
            self.bot,
            interaction.guild,
            interaction.channel,
            interaction.user,
            f"/{command_name}",
            "Slash command used.",
        )


async def setup(bot):
    await bot.add_cog(ModLog(bot))
