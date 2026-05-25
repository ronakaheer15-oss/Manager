import discord
from discord import app_commands
from discord.ext import commands
from config import EMBED_COLOR
from utils.checks import is_staff, is_manager
import datetime

class Scrims(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="scrimcreate", description="Schedule a new scrim")
    @is_manager()
    async def scrimcreate(self, interaction: discord.Interaction, opponent: str, date: str, notes: str = "N/A"):
        try:
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M")
        except ValueError:
            await interaction.response.send_message("❌ Invalid date format. Use YYYY-MM-DD HH:MM (e.g., 2026-05-15 21:00).", ephemeral=True)
            return

        await self.bot.db.create_scrim(str(date_obj), opponent, notes)
        
        embed = discord.Embed(title="📅 New Scrim Scheduled", color=EMBED_COLOR)
        embed.add_field(name="Opponent", value=opponent, inline=True)
        embed.add_field(name="Date & Time", value=str(date_obj), inline=True)
        embed.add_field(name="Notes", value=notes, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="scrimresult", description="Log the result of a scrim")
    @is_staff()
    async def scrimresult(self, interaction: discord.Interaction, scrim_id: int, result: str):
        await self.bot.db.update_scrim_result(scrim_id, result)
        await interaction.response.send_message(f"✅ Result updated for Scrim ID #{scrim_id}: **{result}**")

    @app_commands.command(name="scrimhistory", description="View recent scrim history")
    async def scrimhistory(self, interaction: discord.Interaction):
        history = await self.bot.db.get_scrim_history()
        
        if not history:
            await interaction.response.send_message("No scrim history found.", ephemeral=True)
            return

        embed = discord.Embed(title="📜 Recent Scrim History", color=EMBED_COLOR)
        for s in history:
            # s: (id, date, opponent, result, notes, reminders_sent)
            result_text = s[3] if s[3] else "Pending"
            embed.add_field(name=f"ID #{s[0]} vs {s[2]}", value=f"Date: {s[1]}\nResult: {result_text}", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="matchday", description="Generate a Match Day announcement graphic")
    @app_commands.describe(opponent="Opponent Team Name", time="Match Time")
    @is_manager()
    async def matchday(self, interaction: discord.Interaction, opponent: str, time: str):
        embed = discord.Embed(title="🔥 IT'S MATCH DAY! 🔥", description="The Kree Esports roster is stepping onto the battlefield today.", color=0xFF4500)
        embed.add_field(name="🆚 Opponent", value=f"**{opponent}**", inline=True)
        embed.add_field(name="⏰ Time", value=f"**{time}**", inline=True)
        embed.set_image(url="https://i.imgur.com/z8pG2uA.png") # Placeholder dynamic graphic
        embed.set_footer(text="Drop a 🔥 in chat to support the team!")
        
        channel_id = await self.bot.db.get_setting("announcement_channel")
        channel = self.bot.get_channel(int(channel_id)) if channel_id else interaction.channel
        
        await channel.send(content="@everyone", embed=embed)
        await interaction.response.send_message("✅ Match Day graphic posted!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Scrims(bot))

