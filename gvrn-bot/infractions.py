import os

import discord
from discord.ext import commands

INFRACTION_LOG_CHANNEL_ID = int(os.getenv("INFRACTION_LOG_CHANNEL_ID", "0"))
INFRACTION_1_ROLE_ID = int(os.getenv("INFRACTION_1_ROLE_ID", "0"))
INFRACTION_2_ROLE_ID = int(os.getenv("INFRACTION_2_ROLE_ID", "0"))
INFRACTION_3_ROLE_ID = int(os.getenv("INFRACTION_3_ROLE_ID", "0"))
INFRACTION_COMMAND_ROLE_ID = int(os.getenv("INFRACTION_COMMAND_ROLE_ID", "0"))

INFRACTION_COLOR = 0x76F55D
INFRACTION_APPEAL_TEXT = os.getenv("INFRACTION_APPEAL_TEXT", "appeal here")
INFRACTION_SERVER_NAME = "Greenville Community Roleplay"


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

        role_ids = {
            1: INFRACTION_1_ROLE_ID,
            2: INFRACTION_2_ROLE_ID,
            3: INFRACTION_3_ROLE_ID,
        }

        role = ctx.guild.get_role(role_ids[level])

        if role is None:
            await ctx.send(f"Infraction {level} role was not found. Check your .env role ID.")
            return

        proof_links = collect_proof(ctx)
        reason_and_evidence = reason

        if proof_links:
            reason_and_evidence += "\n" + "\n".join(proof_links)

        try:
            await member.add_roles(role, reason=f"Infraction {level}: {reason} | Issued by {ctx.author}")
        except discord.Forbidden:
            await ctx.send("I cannot give that infraction role. Move my bot role above it.")
            return

        notice_embed = discord.Embed(
            description=(
                f"✅ **{member.display_name} has been warned.** || "
                f"__Infraction Notice__: {INFRACTION_SERVER_NAME}\n\n"
                f"> • **Dear user, you received an __Infraction__ in GVCR due to:**\n\n"
                f"Reason & Evidence: **{reason_and_evidence}**\n\n"
                f"**If you believe that this**\n"
                f"Infraction **is false, please DM a Staff Team member or appeal {INFRACTION_APPEAL_TEXT}.**\n\n"
                f"**Signed,**\n"
                f"{ctx.author.mention}"
            ),
            color=INFRACTION_COLOR,
        )

        confirm_embed = discord.Embed(
            description=(
                f"✅ **Added Infraction {level}/3 to {member.display_name}.** "
                f"|| {reason if reason else 'No reason given.'}"
            ),
            color=INFRACTION_COLOR,
        )

        dm_embed = discord.Embed(
            description=(
                f"You were warned in **GVRN** for\n"
                f"Dear {member.display_name}, you have been issued an **Infraction {level}** "
                f"within Greenville Roleplay Network due to the following reason:\n\n"
                f"• Reason: {reason}\n"
                f"• Evidence: {chr(10).join(proof_links) if proof_links else 'No evidence provided'}\n\n"
                f"**If you believe this moderation is false, please talk to a Staff Team member or appeal.**\n\n"
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
            log_embed = discord.Embed(
                title=f"Infraction {level} Logged",
                color=INFRACTION_COLOR,
            )
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


async def setup(bot):
    await bot.add_cog(Infractions(bot))
