import json
import os
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.ext import commands

INFRACTION_LOG_CHANNEL_ID = int(os.getenv("INFRACTION_LOG_CHANNEL_ID", "0"))
INFRACTION_1_ROLE_ID = int(os.getenv("INFRACTION_1_ROLE_ID", "0"))
INFRACTION_2_ROLE_ID = int(os.getenv("INFRACTION_2_ROLE_ID", "0"))
INFRACTION_3_ROLE_ID = int(os.getenv("INFRACTION_3_ROLE_ID", "0"))
INFRACTION_COMMAND_ROLE_ID = int(os.getenv("INFRACTION_COMMAND_ROLE_ID", "0"))

INFRACTION_COLOR = 0xEAC5FD
INFRACTION_APPEAL_TEXT = os.getenv("INFRACTION_APPEAL_TEXT", "by opening an appeal application")
INFRACTION_SERVER_NAME = "Greenville Roleplay Network"
INFRACTION_DATA_FILE = Path("infraction_cases.json")


def load_cases():
    if not INFRACTION_DATA_FILE.exists():
        return {
            "counter": 0,
            "cases": [],
        }

    with INFRACTION_DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_cases(data):
    with INFRACTION_DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def next_case_id(data):
    data["counter"] += 1
    return f"INF-{data['counter']:04d}"


def can_issue_infraction(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(role.id == INFRACTION_COMMAND_ROLE_ID for role in member.roles)


async def resolve_member(ctx, user_text: str):
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


def collect_proof(ctx):
    links = []

    for attachment in ctx.message.attachments:
        links.append(attachment.url)

    return links


def get_role_id_for_level(level: int):
    role_ids = {
        1: INFRACTION_1_ROLE_ID,
        2: INFRACTION_2_ROLE_ID,
        3: INFRACTION_3_ROLE_ID,
    }
    return role_ids[level]


def find_case(data, case_id: str):
    for case in data["cases"]:
        if case["case_id"].lower() == case_id.lower():
            return case

    return None


class Infractions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def issue_infraction(self, ctx, level: int, user_text: str, reason: str):
        if not can_issue_infraction(ctx.author):
            await ctx.send("You need the Staff Team role to use this command.")
            return

        member = await resolve_member(ctx, user_text)

        if member is None:
            await ctx.send("Could not find that user. Use a Discord user ID or mention.")
            return

        role = ctx.guild.get_role(get_role_id_for_level(level))

        if role is None:
            await ctx.send(f"Infraction {level} role was not found. Check your .env role ID.")
            return

        proof_links = collect_proof(ctx)
        reason_and_evidence = reason

        if proof_links:
            reason_and_evidence += "\n" + "\n".join(proof_links)

        data = load_cases()
        case_id = next_case_id(data)

        case = {
            "case_id": case_id,
            "active": True,
            "level": level,
            "user_id": member.id,
            "user_name": str(member),
            "issuer_id": ctx.author.id,
            "issuer_name": str(ctx.author),
            "reason": reason,
            "evidence": proof_links,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "revoked_at": None,
            "revoked_by": None,
            "revoke_reason": None,
        }

        data["cases"].append(case)
        save_cases(data)

        try:
            await member.add_roles(role, reason=f"{case_id} Infraction {level}: {reason} | Issued by {ctx.author}")
        except discord.Forbidden:
            await ctx.send("I cannot give that infraction role. Move my bot role above it.")
            return

        notice_embed = discord.Embed(
            description=(
                f"✅ **{member.display_name} has been warned.** || "
                f"__Infraction Notice__: {INFRACTION_SERVER_NAME}\n\n"
                f"> • **Dear user, you received an __Infraction__ in GVRN due to:**\n\n"
                f"**Case:** `{case_id}`\n"
                f"Reason & Evidence: **{reason_and_evidence}**\n\n"
                f"**If you believe that this**\n"
                f"Infraction **is false, please DM a Staff Team member or {INFRACTION_APPEAL_TEXT}.**\n\n"
                f"**Signed,**\n"
                f"{ctx.author.mention}"
            ),
            color=INFRACTION_COLOR,
        )

        confirm_embed = discord.Embed(
            description=(
                f"✅ **Added Infraction {level}/3 to {member.display_name}.** "
                f"|| Case `{case_id}` | {reason if reason else 'No reason given.'}"
            ),
            color=INFRACTION_COLOR,
        )

        dm_embed = discord.Embed(
            description=(
                f"You were warned in **{INFRACTION_SERVER_NAME}**.\n"
                f"Dear {member.display_name}, you have been issued **Infraction {level}** "
                f"due to the following reason:\n\n"
                f"• Case: `{case_id}`\n"
                f"• Reason: {reason}\n"
                f"• Evidence: {chr(10).join(proof_links) if proof_links else 'No evidence provided'}\n\n"
                f"**If you believe this moderation is false, please talk to a Staff Team member or {INFRACTION_APPEAL_TEXT}.**\n\n"
                f"**Signed,**\n"
                f"{ctx.author}\n"
                f"Staff Team"
            ),
            color=INFRACTION_COLOR,
        )

        try:
            await member.send(embed=dm_embed)
            dm_status = "DM sent."
        except discord.HTTPException:
            dm_status = "Could not DM user."

        await ctx.send(embed=notice_embed)
        await ctx.send(embed=confirm_embed)
        await ctx.send(dm_status)

        log_channel = ctx.guild.get_channel(INFRACTION_LOG_CHANNEL_ID)
        if isinstance(log_channel, discord.TextChannel):
            log_embed = discord.Embed(title=f"{case_id} | Infraction {level} Logged", color=INFRACTION_COLOR)
            log_embed.add_field(name="User", value=f"{member.mention} (`{member.id}`)", inline=False)
            log_embed.add_field(name="Issued By", value=ctx.author.mention, inline=False)
            log_embed.add_field(name="Reason / Evidence", value=reason_and_evidence[:1000], inline=False)
            log_embed.add_field(name="Role Given", value=role.mention, inline=False)
            await log_channel.send(embed=log_embed)

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

    @commands.command(name="infraction1")
    async def infraction1(self, ctx, user_text: str, *, reason: str = "No reason given."):
        await self.issue_infraction(ctx, 1, user_text, reason)

    @commands.command(name="infraction2")
    async def infraction2(self, ctx, user_text: str, *, reason: str = "No reason given."):
        await self.issue_infraction(ctx, 2, user_text, reason)

    @commands.command(name="infraction3")
    async def infraction3(self, ctx, user_text: str, *, reason: str = "No reason given."):
        await self.issue_infraction(ctx, 3, user_text, reason)

    @commands.command(name="modlog")
    async def modlog(self, ctx, user_text: str = None):
        if not can_issue_infraction(ctx.author):
            await ctx.send("You need the Staff Team role to use this command.")
            return

        data = load_cases()
        cases = data["cases"]

        target_member = None
        if user_text:
            target_member = await resolve_member(ctx, user_text)
            if target_member is None:
                await ctx.send("Could not find that user. Use a Discord user ID or mention.")
                return
            cases = [case for case in cases if str(case["user_id"]) == str(target_member.id)]

        if not cases:
            await ctx.send("No infraction cases found.")
            return

        lines = []
        for case in cases[-25:]:
            status = "Active" if case["active"] else "Revoked"
            lines.append(
                f"`{case['case_id']}` | {status} | Infraction {case['level']} | "
                f"{case['user_name']} | {case['reason']}"
            )

        title = "Infraction Modlog"
        if target_member:
            title += f" for {target_member.display_name}"

        embed = discord.Embed(title=title, description="\n".join(lines), color=INFRACTION_COLOR)
        await ctx.send(embed=embed)

    @commands.command(name="revoke")
    async def revoke(self, ctx, case_id: str, *, reason: str = "No reason provided."):
        if not can_issue_infraction(ctx.author):
            await ctx.send("You need the Staff Team role to use this command.")
            return

        data = load_cases()
        case = find_case(data, case_id)

        if not case:
            await ctx.send("Case not found.")
            return

        if not case["active"]:
            await ctx.send("That case is already revoked.")
            return

        case["active"] = False
        case["revoked_at"] = datetime.now(timezone.utc).isoformat()
        case["revoked_by"] = str(ctx.author)
        case["revoke_reason"] = reason
        case["updated_at"] = datetime.now(timezone.utc).isoformat()
        save_cases(data)

        member = await resolve_member(ctx, str(case["user_id"]))
        role = ctx.guild.get_role(get_role_id_for_level(case["level"]))

        if member and role and role in member.roles:
            try:
                await member.remove_roles(role, reason=f"{case_id} revoked by {ctx.author}: {reason}")
            except discord.Forbidden:
                await ctx.send("Case revoked, but I could not remove the role.")

        await ctx.send(f"Revoked `{case_id}`. Reason: {reason}")

    @commands.command(name="edit")
    async def edit_case(self, ctx, case_id: str, *, new_reason: str):
        if not can_issue_infraction(ctx.author):
            await ctx.send("You need the Staff Team role to use this command.")
            return

        data = load_cases()
        case = find_case(data, case_id)

        if not case:
            await ctx.send("Case not found.")
            return

        old_reason = case["reason"]
        case["reason"] = new_reason
        case["updated_at"] = datetime.now(timezone.utc).isoformat()
        save_cases(data)

        await ctx.send(f"Edited `{case_id}`.\nOld: {old_reason}\nNew: {new_reason}")


async def setup(bot):
    await bot.add_cog(Infractions(bot))
