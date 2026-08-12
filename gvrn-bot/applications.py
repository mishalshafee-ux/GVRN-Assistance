import io
import json
import os
from pathlib import Path

import discord
from discord.ext import commands

APPLICATION_PANEL_CHANNEL_ID = int(os.getenv("APPLICATION_PANEL_CHANNEL_ID", "0"))
LICENSE_APPLICATION_LOG_CHANNEL_ID = int(os.getenv("LICENSE_APPLICATION_LOG_CHANNEL_ID", "0"))
STAFF_APPLICATION_LOG_CHANNEL_ID = int(os.getenv("STAFF_APPLICATION_LOG_CHANNEL_ID", "0"))
APPEAL_APPLICATION_LOG_CHANNEL_ID = int(os.getenv("APPEAL_APPLICATION_LOG_CHANNEL_ID", "0"))
HIGH_COMMAND_ROLE_ID = int(os.getenv("HIGH_COMMAND_ROLE_ID", "0"))

APPLICATION_DATA_FILE = Path("application_status.json")

PANEL_COLOR = 0x76F55D
OPEN_MARK = os.getenv("APP_OPEN_EMOJI", "✅")
CLOSED_MARK = os.getenv("APP_CLOSED_EMOJI", "❌")

APPLICATIONS = {
    "license": {
        "name": "License Quiz",
        "log_channel_id": LICENSE_APPLICATION_LOG_CHANNEL_ID,
        "questions": [
            "What is your Roblox username?",
            "What is your Discord User ID?",
            "Are you 13 years old or older?",
            "What does a red traffic light mean?",
            "What does a yellow traffic light mean?",
            "What should you do when approaching a stop sign?",
            "What is the purpose of a speed limit?",
            "When should you use your turn signal?",
            "What should you do when an emergency vehicle approaches with lights and sirens?",
            "What does reckless driving mean?",
            "What should you do before changing lanes?",
            "What is tailgating?",
            "When is it appropriate to use your vehicle's horn?",
            "What should you do if you are involved in a traffic accident?",
            "Why is following traffic laws important during roleplay?",
        ],
    },
    "staff": {
        "name": "Staff Application",
        "log_channel_id": STAFF_APPLICATION_LOG_CHANNEL_ID,
        "questions": [
            "What is your Roblox username?",
            "What is your Discord User ID?",
            "Are you 13 years old or older?",
            "Why do you want to become a staff member?",
            "What makes you suitable for the staff team?",
            "What does being a good staff member mean to you?",
            "How would you handle a member who is breaking the rules?",
            "What would you do if a friend of yours broke a server rule?",
            "How would you deal with an angry or disrespectful member?",
            "What would you do if you were unsure how to handle a situation?",
            "Why is it important for staff to remain professional?",
            "What would you do if another staff member was abusing their permissions?",
            "How active can you be within the server?",
            "How would you handle confidential staff information?",
            "Why should we choose you over other applicants?",
        ],
    },
    "appeal": {
        "name": "Appeal Application",
        "log_channel_id": APPEAL_APPLICATION_LOG_CHANNEL_ID,
        "questions": [
            "What is your Roblox username?",
            "What is your Discord User ID?",
            "What is the Discord username of the person appealing?",
            "What type of infraction are you appealing?",
            "Who issued the infraction?",
            "What was the reason given for the infraction?",
            "When was the infraction issued?",
            "Why do you believe the infraction should be removed or reduced?",
            "What happened from your perspective?",
            "Do you accept responsibility for any part of the incident?",
            "Do you have any evidence supporting your appeal?",
            "Were there any circumstances that may have contributed to the incident?",
            "Have you received any previous infractions?",
            "What will you do to prevent a similar situation from happening again?",
            "Is there anything else you would like the reviewing staff team to consider?",
        ],
    },
}


def is_high_command(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(role.id == HIGH_COMMAND_ROLE_ID for role in member.roles)


def load_statuses():
    if not APPLICATION_DATA_FILE.exists():
        return {
            "license": True,
            "staff": True,
            "appeal": True,
            "panel_channel_id": None,
            "panel_message_id": None,
        }

    with APPLICATION_DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_statuses(statuses):
    with APPLICATION_DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(statuses, file, indent=2)


def build_panel_message():
    statuses = load_statuses()
    lines = [
        "# 💬 Greenville Roleplay Network | Applications 💬",
        "",
        f"➜ Applications marked with {OPEN_MARK} are **open**. Applications marked with {CLOSED_MARK} are **closed**.",
        "Please only apply to open applications, as closed applications will not be evaluated.",
        "",
    ]

    for key, app in APPLICATIONS.items():
        is_open = statuses.get(key, True)
        mark = OPEN_MARK if is_open else CLOSED_MARK
        action_text = "**Click the button below**" if is_open else "**CLOSED**"
        lines.append(f"• {app['name']} {mark} {action_text}")
        lines.append("")

    lines.append("For any additional questions or concerns, please contact the Application Team.")
    return "\n".join(lines)


class ApplicationPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for key, app in APPLICATIONS.items():
            self.add_item(ApplicationButton(key, app["name"]))


class ApplicationButton(discord.ui.Button):
    def __init__(self, app_key: str, label: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.success,
            custom_id=f"application_button_{app_key}",
        )
        self.app_key = app_key

    async def callback(self, interaction: discord.Interaction):
        statuses = load_statuses()

        if not statuses.get(self.app_key, True):
            await interaction.response.send_message("This application is currently closed.", ephemeral=True)
            return

        await interaction.response.send_modal(ApplicationModal(self.app_key, 0, []))


class ContinueApplicationView(discord.ui.View):
    def __init__(self, app_key: str, page: int, answers: list[str]):
        super().__init__(timeout=300)
        self.app_key = app_key
        self.page = page
        self.answers = answers

    @discord.ui.button(label="Continue Application", style=discord.ButtonStyle.success)
    async def continue_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal(self.app_key, self.page, self.answers))


class ApplicationModal(discord.ui.Modal):
    def __init__(self, app_key: str, page: int, previous_answers: list[str]):
        app = APPLICATIONS[app_key]
        super().__init__(title=f"{app['name']} - Part {page + 1}")

        self.app_key = app_key
        self.page = page
        self.previous_answers = previous_answers

        questions = app["questions"][page * 5 : page * 5 + 5]
        self.inputs = []

        for question in questions:
            field = discord.ui.TextInput(
                label=question[:45],
                placeholder=question,
                style=discord.TextStyle.paragraph,
                required=True,
                max_length=1000,
            )
            self.inputs.append(field)
            self.add_item(field)

    async def on_submit(self, interaction: discord.Interaction):
        answers = self.previous_answers + [field.value for field in self.inputs]
        questions = APPLICATIONS[self.app_key]["questions"]
        next_page = self.page + 1

        if next_page * 5 < len(questions):
            await interaction.response.send_message(
                f"Part {self.page + 1} saved. Click below for the next part.",
                view=ContinueApplicationView(self.app_key, next_page, answers),
                ephemeral=True,
            )
            return

        await send_application(interaction, self.app_key, answers)


async def send_application(interaction: discord.Interaction, app_key: str, answers: list[str]):
    app = APPLICATIONS[app_key]
    log_channel = interaction.guild.get_channel(app["log_channel_id"])

    if not isinstance(log_channel, discord.TextChannel):
        await interaction.response.send_message(
            "Application log channel is not set correctly.",
            ephemeral=True,
        )
        return

    lines = [
        f"{app['name']} Submission",
        f"Submitted by: {interaction.user} ({interaction.user.id})",
        "",
    ]

    for index, question in enumerate(app["questions"], start=1):
        answer = answers[index - 1] if index - 1 < len(answers) else "No answer."
        lines.append(f"{index}. {question}")
        lines.append(answer)
        lines.append("")

    transcript = "\n".join(lines)

    file = discord.File(
        fp=io.StringIO(transcript),
        filename=f"{app_key}_application_{interaction.user.id}.txt",
    )

    embed = discord.Embed(
        title=f"New {app['name']} Submission",
        description=f"Submitted by {interaction.user.mention}",
        color=PANEL_COLOR,
    )
    embed.add_field(name="User ID", value=str(interaction.user.id), inline=False)

    await log_channel.send(embed=embed, file=file)
    await interaction.response.send_message("Your application has been submitted.", ephemeral=True)


class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(ApplicationPanelView())

    @commands.command(name="lpanel")
    @commands.has_permissions(administrator=True)
    async def lpanel(self, ctx):
        channel = ctx.guild.get_channel(APPLICATION_PANEL_CHANNEL_ID)

        if not isinstance(channel, discord.TextChannel):
            await ctx.send("Application panel channel not found. Check APPLICATION_PANEL_CHANNEL_ID.")
            return

        message = await channel.send(content=build_panel_message(), view=ApplicationPanelView())

        statuses = load_statuses()
        statuses["panel_channel_id"] = channel.id
        statuses["panel_message_id"] = message.id
        save_statuses(statuses)

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

    @commands.command(name="appstatus")
    async def appstatus(self, ctx, application: str, status: str):
        if not is_high_command(ctx.author):
            await ctx.send("You need High Command+ to use this command.")
            return

        application = application.lower()
        status = status.lower()

        if application not in APPLICATIONS:
            await ctx.send("Use one of: `license`, `staff`, `appeal`.")
            return

        if status not in ["open", "closed"]:
            await ctx.send("Status must be `open` or `closed`.")
            return

        statuses = load_statuses()
        statuses[application] = status == "open"
        save_statuses(statuses)

        panel_channel_id = statuses.get("panel_channel_id")
        panel_message_id = statuses.get("panel_message_id")

        if panel_channel_id and panel_message_id:
            panel_channel = ctx.guild.get_channel(panel_channel_id)
            if isinstance(panel_channel, discord.TextChannel):
                try:
                    panel_message = await panel_channel.fetch_message(panel_message_id)
                    await panel_message.edit(content=build_panel_message(), embed=None, view=ApplicationPanelView())
                except discord.HTTPException:
                    pass

        await ctx.send(f"{APPLICATIONS[application]['name']} is now **{status}**.")


async def setup(bot):
    await bot.add_cog(Applications(bot))
