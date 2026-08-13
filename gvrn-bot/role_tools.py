import os

import discord
from discord.ext import commands

HIGH_COMMAND_ROLE_ID = int(os.getenv("HIGH_COMMAND_ROLE_ID", "0"))


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


def resolve_role(guild, role_text):
    role_text = role_text.strip()

    if role_text.startswith("<@&") and role_text.endswith(">"):
        role_id = role_text.replace("<@&", "").replace(">", "")
        if role_id.isdigit():
            return guild.get_role(int(role_id))

    if role_text.isdigit():
        return guild.get_role(int(role_text))

    lowered = role_text.lower()
    return discord.utils.find(lambda role: role.name.lower() == lowered, guild.roles)


def parse_roles_and_reason(guild, text):
    if "|" in text:
        roles_part, reason = text.split("|", 1)
        role_names = [item.strip() for item in roles_part.split(",") if item.strip()]
        roles = [resolve_role(guild, role_name) for role_name in role_names]
        roles = [role for role in roles if role is not None]
        return roles, reason.strip() or "No reason provided."

    words = text.split()
    best_role = None
    best_index = 0

    for index in range(len(words), 0, -1):
        possible_name = " ".join(words[:index])
        role = resolve_role(guild, possible_name)
        if role:
            best_role = role
            best_index = index
            break

    if not best_role:
        return [], "No reason provided."

    reason = " ".join(words[best_index:]).strip() or "No reason provided."
    return [best_role], reason


class RoleTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="role")
    async def role(self, ctx, user_text: str, *, role_text: str):
        if not can_use_role_command(ctx.author):
            await ctx.send("You need High Command+ to use this command.")
            return

        member = await resolve_member(ctx, user_text)

        if member is None:
            await ctx.send("Could not find that user. Use a mention or user ID.")
            return

        roles, reason = parse_roles_and_reason(ctx.guild, role_text)

        if not roles:
            await ctx.send("Could not find that role. Example: `!role @user Staff Team | reason`")
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

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass


async def setup(bot):
    await bot.add_cog(RoleTools(bot))
