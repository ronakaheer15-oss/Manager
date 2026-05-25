import discord
from discord import app_commands
from discord.ext import commands

class Marketplace(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="challenge_post", description="Post a scrim challenge for other teams to see")
    @app_commands.describe(opponent="Your Team Name", contact="Discord ID/Phone", details="T1/T2, Map, Time")
    async def challenge_post(self, interaction: discord.Interaction, opponent: str, contact: str, details: str):
        # Post to the marketplace channel
        channel_id = await self.bot.db.get_setting("announcement_channel") # Or create a marketplace channel
        channel = self.bot.get_channel(int(channel_id)) if channel_id else interaction.channel

        embed = discord.Embed(title="⚔️ New Scrim Challenge!", color=discord.Color.gold())
        embed.add_field(name="Opponent", value=opponent, inline=True)
        embed.add_field(name="Contact", value=contact, inline=True)
        embed.add_field(name="Details", value=details, inline=False)
        embed.set_footer(text="Managers: Contact them to accept!")
        
        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Challenge posted to the marketplace!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Marketplace(bot))
