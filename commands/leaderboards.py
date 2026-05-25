import discord
from discord import app_commands
from discord.ext import commands
from config import EMBED_COLOR

class Leaderboards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="View the team leaderboards")
    @app_commands.choices(category=[
        app_commands.Choice(name="Kills", value="kills"),
        app_commands.Choice(name="MVP", value="mvp"),
        app_commands.Choice(name="Performance Rating", value="rating")
    ])
    async def leaderboard(self, interaction: discord.Interaction, category: str = "kills", post_to_channel: bool = False):
        results = await self.bot.db.get_leaderboard(category)
        
        if not results:
            await interaction.response.send_message("No data available for this leaderboard.", ephemeral=True)
            return

        embed = discord.Embed(title=f"🏆 Top 10 Leaderboard - {category.capitalize()}", color=EMBED_COLOR)
        
        leaderboard_text = ""
        for i, (ign, total) in enumerate(results, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
            leaderboard_text += f"{medal} **{ign}**: {total}\n"
        
        embed.description = leaderboard_text
        
        if post_to_channel:
            channel_id = await self.bot.db.get_setting("leaderboard_channel")
            channel = self.bot.get_channel(int(channel_id)) if channel_id else interaction.channel
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Leaderboard posted to {channel.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Leaderboards(bot))
