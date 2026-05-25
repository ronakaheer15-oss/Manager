import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
from config import EMBED_COLOR
from utils.checks import is_staff

class Playbook(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="playbook_add", description="Add a strategy or training material to the playbook")
    @app_commands.describe(title="Title of the strategy", link="Link to image/video/doc", category="Erangel, Rotations, etc.")
    @is_staff()
    async def playbook_add(self, interaction: discord.Interaction, title: str, link: str, category: str):
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            await db.execute("INSERT INTO playbook (title, strategy_link, category, added_by) VALUES (?, ?, ?, ?)", (title, link, category, interaction.user.id))
            await db.commit()
        await interaction.response.send_message(f"📚 Added **{title}** to the **{category}** section of the Playbook!")

    @app_commands.command(name="playbook", description="View the organization's training and strategy database")
    @is_staff()
    async def playbook(self, interaction: discord.Interaction):
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            async with db.execute("SELECT title, strategy_link, category FROM playbook ORDER BY category") as cursor:
                rows = await cursor.fetchall()
        
        if not rows:
            await interaction.response.send_message("📚 The playbook is currently empty. Staff can add strategies with `/playbook_add`.")
            return

        embed = discord.Embed(title="📚 Organization Playbook", color=discord.Color.blue())
        for row in rows:
            # row: (title, link, category)
            embed.add_field(name=f"📂 {row[2]}", value=f"🔗 [{row[0]}]({row[1]})", inline=True)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Playbook(bot))
