import discord
from discord import app_commands
from discord.ext import commands
from config import EMBED_COLOR
from utils.checks import is_staff
import datetime

class Attendance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="attendance", description="Mark attendance for a player")
    @app_commands.choices(status=[
        app_commands.Choice(name="Joined", value="Joined"),
        app_commands.Choice(name="Skipped", value="Skipped"),
        app_commands.Choice(name="Late", value="Late")
    ])
    @is_staff()
    async def attendance(self, interaction: discord.Interaction, member: discord.Member, status: str, date: str = None):
        try:
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date() if date else datetime.date.today()
        except ValueError:
            await interaction.response.send_message("❌ Invalid date format. Use YYYY-MM-DD.", ephemeral=True)
            return
        
        player = await self.bot.db.get_player(member.id)
        if not player:
            await interaction.response.send_message(f"❌ {member.display_name} doesn't have a profile yet.", ephemeral=True)
            return

        await self.bot.db.add_attendance(member.id, str(date_obj), status)
        await interaction.response.send_message(f"✅ Attendance marked for {member.mention}: **{status}** on {date_obj}")

    @app_commands.command(name="activity", description="View attendance report for a specific date")
    @is_staff()
    async def activity(self, interaction: discord.Interaction, date: str = None):
        try:
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date() if date else datetime.date.today()
        except ValueError:
            await interaction.response.send_message("❌ Invalid date format. Use YYYY-MM-DD.", ephemeral=True)
            return

        report = await self.bot.db.get_attendance_report(str(date_obj))
        
        if not report:
            await interaction.response.send_message(f"No attendance data found for {date_obj}.", ephemeral=True)
            return

        embed = discord.Embed(title=f"📅 Attendance Report - {date_obj}", color=EMBED_COLOR)
        joined = [r[0] for r in report if r[1] == "Joined"]
        skipped = [r[0] for r in report if r[1] == "Skipped"]
        late = [r[0] for r in report if r[1] == "Late"]

        embed.add_field(name="✅ Joined", value="\n".join(joined) or "None", inline=True)
        embed.add_field(name="❌ Skipped", value="\n".join(skipped) or "None", inline=True)
        embed.add_field(name="⏰ Late", value="\n".join(late) or "None", inline=True)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Attendance(bot))

