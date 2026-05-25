import discord
from discord import app_commands
from discord.ext import commands
from config import EMBED_COLOR
from utils.checks import is_staff

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="wallet", description="Check your team coin balance")
    async def wallet(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        balance = await self.bot.db.get_balance(member.id)
        
        embed = discord.Embed(title="💰 Team Wallet", color=0xF1C40F)
        embed.add_field(name="Player", value=member.mention, inline=True)
        embed.add_field(name="Balance", value=f"{balance} Kree Coins", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reward", description="Reward a player with team coins")
    @is_staff()
    async def reward(self, interaction: discord.Interaction, member: discord.Member, amount: int, reason: str):
        await self.bot.db.update_balance(member.id, amount)
        await interaction.response.send_message(f"✅ Rewarded {member.mention} with **{amount}** Kree Coins for: {reason}")

    @app_commands.command(name="shop", description="View the team shop")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🏪 Kree Esports Shop", color=0x3498DB)
        embed.add_field(name="Custom Role (1 Week)", value="500 Coins", inline=False)
        embed.add_field(name="Priority Scrim Slot", value="200 Coins", inline=False)
        embed.add_field(name="Team Shoutout", value="100 Coins", inline=False)
        embed.set_footer(text="Use coins earned from MVPs and Practice to buy rewards!")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))

