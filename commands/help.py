import discord
from discord import app_commands
from discord.ext import commands
from config import EMBED_COLOR, BOT_NAME

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="View the complete KreeManager Organization Manual")
    async def help(self, interaction: discord.Interaction):
        # We use a simple defer if the embed is large, though usually not needed for help
        # await interaction.response.defer(ephemeral=False) 
        
        embed = discord.Embed(title=f"📖 {BOT_NAME} - Complete Organization Manual", color=EMBED_COLOR)
        embed.description = "Welcome to your organization's command center. Here is how to use 100% of the bot's power."

        embed.add_field(name="🏢 ORGANIZATION MGMT", value=(
            "`/setup_server`: Create premium categories & permissions.\n"
            "`/create_team`: Add new teams to your org.\n"
            "`/assign_role`: Give roles (IGL, Sniper, Coach, etc.).\n"
            "`/check_inactivity`: Find and warn silent players."
        ), inline=False)

        embed.add_field(name="🤖 AI AUTOMATION (KreeRank Merge)", value=(
            "`/set_report_channel`: Bot will auto-parse screenshots here.\n"
            "**Auto-Tracking**: Just post a match screenshot, AI does the rest!\n"
            "**Interactive Mapping**: Bot DMs you to link unknown players.\n"
            "**NLP Parsing**: Send 'Log 5 kills for Ronak' and it works!"
        ), inline=False)


        embed.add_field(name="🎮 PERFORMANCE & STATS", value=(
            "`/logstats`: Log kills, assists, and performance.\n"
            "`/leaderboard`: View top players in the organization.\n"
            "`/profile`: View a player's professional card.\n"
            "`/team`: View full roster and sub-team Win Rates.\n"
            "`/matchday`: Post professional match graphics."
        ), inline=False)

        embed.add_field(name="🛡️ DISCIPLINE & ROSTER", value=(
            "`/warn`: Issue a formal warning.\n"
            "`/bench`: Move a player to the inactive roster.\n"
            "`/kick` / `/ban`: Remove players from the server.\n"
            "`/request_vacation`: Ask for leave (Staff approves).\n"
            "`/approve_vacation`: Grant a player's leave request."
        ), inline=False)

        embed.add_field(name="🏦 FINANCE & LOGISTICS", value=(
            "`/ledger_add`: Add tournament entry fees/debts.\n"
            "`/ledger_view`: Track organizational finances.\n"
            "`/ledger_pay`: Mark a debt as settled.\n"
            "`/scrim_challenge`: Post to the marketplace."
        ), inline=False)

        embed.add_field(name="🧠 COACH'S TOOLS", value=(
            "`/playbook_add`: Add strategy links/guides.\n"
            "`/playbook`: View the tactical database.\n"
            "`/approve_action`: Approve staff role requests."
        ), inline=False)

        embed.set_footer(text="🔥 KreeManager: Professional Esports Excellence.")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
