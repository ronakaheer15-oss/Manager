import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
from config import EMBED_COLOR
from utils.checks import is_staff

class Performance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="logstats", description="Log performance stats for a player")
    @app_commands.describe(map_name="The map played")
    @app_commands.choices(map_name=[
        app_commands.Choice(name="Erangel", value="Erangel"),
        app_commands.Choice(name="Miramar", value="Miramar"),
        app_commands.Choice(name="Sanhok", value="Sanhok"),
        app_commands.Choice(name="Vikendi", value="Vikendi"),
        app_commands.Choice(name="Nusa", value="Nusa")
    ])
    @is_staff()
    async def logstats(self, interaction: discord.Interaction, member: discord.Member, kills: int, assists: int, survival: int, map_name: str, clutches: int = 0, teamplay: int = 5, communication: int = 5, discipline: int = 5, mistakes: int = 0):


        player = await self.bot.db.get_player(member.id)
        if not player:
            await interaction.response.send_message(f"❌ {member.display_name} doesn't have a profile yet.", ephemeral=True)
            return

        await self.bot.db.add_stats(member.id, kills, assists, survival, clutches, teamplay, communication, discipline, mistakes)
        
        # Log to map_stats
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            result = "Win" if (kills > 5 and mistakes == 0) else "Played"
            await db.execute("INSERT INTO map_stats (map_name, result) VALUES (?, ?)", (map_name, result))
            await db.commit()
        
        # Simple rating calculation
        rating = (kills * 2 + assists + clutches * 5 + teamplay + communication + discipline) - (mistakes * 3)
        
        await interaction.response.send_message(f"✅ Stats logged for {member.mention} on **{map_name}**! Performance Rating: **{rating}**")

async def setup(bot):
    await bot.add_cog(Performance(bot))
