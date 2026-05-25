import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
from config import EMBED_COLOR
from utils.checks import is_manager

class Finance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ledger_add", description="Add an entry fee or debt to a player")
    @app_commands.describe(member="The player", item="Tournament Name/Reason", amount="Amount due")
    @is_manager()
    async def ledger_add(self, interaction: discord.Interaction, member: discord.Member, item: str, amount: float):
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            await db.execute("INSERT INTO ledger (item_name, amount, player_id, status) VALUES (?, ?, ?, 'Unpaid')", (item, amount, member.id))
            await db.commit()
        await interaction.response.send_message(f"💰 Added **{item}** debt of **{amount}** to {member.mention}.")

    @app_commands.command(name="ledger_view", description="View unpaid entry fees and debts")
    @is_manager()
    async def ledger_view(self, interaction: discord.Interaction):
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            async with db.execute("SELECT l.id, p.ign, l.item_name, l.amount FROM ledger l JOIN players p ON l.player_id = p.discord_id WHERE l.status = 'Unpaid'") as cursor:
                rows = await cursor.fetchall()
        
        if not rows:
            await interaction.response.send_message("✅ No pending debts found in the organization.")
            return

        embed = discord.Embed(title="🏦 Financial Ledger - Unpaid Fees", color=discord.Color.red())
        for row in rows:
            # row: (id, ign, item, amount)
            embed.add_field(name=f"ID: {row[0]} | {row[1]}", value=f"**{row[2]}**: {row[3]}", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ledger_pay", description="Mark a debt as paid")
    @is_manager()
    async def ledger_pay(self, interaction: discord.Interaction, id: int):
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            await db.execute("UPDATE ledger SET status = 'Paid' WHERE id = ?", (id,))
            await db.commit()
        await interaction.response.send_message(f"✅ Debt ID #{id} has been marked as **Paid**.")

async def setup(bot):
    await bot.add_cog(Finance(bot))
