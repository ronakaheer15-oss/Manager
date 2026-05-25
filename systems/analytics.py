import discord
from discord import app_commands
from discord.ext import commands
from config import EMBED_COLOR

class Analytics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="analyze", description="AI-driven performance analysis for a player")
    async def analyze(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        stats = await self.bot.db.get_player_stats(member.id)
        
        if not stats:
            await interaction.response.send_message(f"Not enough data to analyze {member.display_name}.", ephemeral=True)
            return

        # stats: list of (id, discord_id, kills, assists, survival, clutches, teamplay, communication, discipline, mistakes, mvp, timestamp)
        total_kills = sum(s[2] for s in stats)
        total_mistakes = sum(s[9] for s in stats)
        avg_kills = total_kills / len(stats)
        
        consistency = "High" if total_mistakes < 2 else "Medium" if total_mistakes < 5 else "Low"
        
        embed = discord.Embed(title=f"🧠 AI Analytics - {member.display_name}", color=0x9B59B6)
        embed.add_field(name="Consistency", value=consistency, inline=True)
        embed.add_field(name="Avg Kills (Last 5)", value=f"{avg_kills:.2f}", inline=True)
        
        # Logic-based suggestions
        suggestions = []
        if total_mistakes > 5:
            suggestions.append("• Work on discipline; reducing mistakes is key.")
        if avg_kills < 2:
            suggestions.append("• Focus on fragging potential and aim training.")
        if sum(s[6] for s in stats) / len(stats) < 4:
            suggestions.append("• Improve teamplay and coordination.")
        
        if not suggestions:
            suggestions.append("• Keep up the great work! Maintain your consistency.")
            
        embed.add_field(name="💡 Suggestions", value="\n".join(suggestions), inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Analytics(bot))
