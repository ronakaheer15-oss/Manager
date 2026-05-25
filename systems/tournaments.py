import discord
from discord import app_commands
from discord.ext import commands
from config import EMBED_COLOR
from utils.checks import is_staff, is_manager
import datetime

class Tournaments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tourney", description="Register a new tournament")
    @is_manager()
    async def tourney(self, interaction: discord.Interaction, name: str, date: str, prize: str):
        try:
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M")
        except ValueError:
            await interaction.response.send_message("❌ Invalid date format. Use YYYY-MM-DD HH:MM.", ephemeral=True)
            return

        await self.bot.db.create_tournament(name, str(date_obj), prize)
        
        embed = discord.Embed(title="🏆 New Tournament Registered", color=EMBED_COLOR)
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Date", value=str(date_obj), inline=True)
        embed.add_field(name="Prize Pool", value=prize, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="match", description="Set Room ID and Password for a tournament match")
    @is_staff()
    async def match(self, interaction: discord.Interaction, tourney_id: int, room_id: str, password: str):
        await self.bot.db.update_tournament_room(tourney_id, room_id, password)
        
        await interaction.response.send_message(f"✅ Room details updated for Tournament ID #{tourney_id}.", ephemeral=True)
        
        # Announcement to configured match channel
        channel_id = await self.bot.db.get_setting("match_channel")
        channel = self.bot.get_channel(int(channel_id)) if channel_id else interaction.channel

        embed = discord.Embed(title="🎮 Room Details Available", color=EMBED_COLOR)
        embed.add_field(name="Room ID", value=room_id, inline=True)
        embed.add_field(name="Password", value=password, inline=True)
        embed.set_footer(text=f"Tournament ID: {tourney_id}")
        
        await channel.send(embed=embed)


    @app_commands.command(name="tourneyhistory", description="View tournament history")
    async def tourneyhistory(self, interaction: discord.Interaction):
        history = await self.bot.db.get_tournaments()
        
        if not history:
            await interaction.response.send_message("No tournaments found.", ephemeral=True)
            return

        embed = discord.Embed(title="🏆 Tournament History", color=EMBED_COLOR)
        for t in history:
            # t: (id, name, date, registration_status, prize, room_id, room_password)
            embed.add_field(name=f"ID #{t[0]}: {t[1]}", value=f"Date: {t[2]}\nPrize: {t[4]}\nStatus: {t[3]}", inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Tournaments(bot))

