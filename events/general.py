import discord
from discord.ext import commands
from discord import app_commands

class GeneralEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: app_commands.Command):
        print(f"[{interaction.user}] Successfully ran: /{command.name}")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            print(f"[{interaction.user}] Is attempting to use: /{interaction.command.name}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        await self.bot.db.update_last_seen(message.author.id)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        from config import ERROR_COLOR
        
        embed = discord.Embed(title="❌ Command Error", color=ERROR_COLOR)
        
        if isinstance(error, app_commands.MissingPermissions):
            embed.description = "You lack the necessary permissions (Administrator/Specific Roles) to run this command."
        elif isinstance(error, app_commands.CommandOnCooldown):
            embed.description = f"This command is on cooldown. Try again in **{error.retry_after:.2f}s**."
        elif isinstance(error, app_commands.CheckFailure):
            embed.description = "Security Check Failed: You do not have the required Staff/Manager role for this action."
        else:
            print(f"Unhandled App Command Error: {error}")
            embed.description = "An unexpected internal error occurred. Our engineers have been notified."

        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GeneralEvents(bot))
