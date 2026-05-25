import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import sys

# Add the current directory to sys.path for easy imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import TOKEN, DATABASE_PATH, BOT_NAME
from database.manager import DatabaseManager

class KreeManager(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.presences = True
        
        super().__init__(
            command_prefix="/",
            intents=intents,
            help_command=None
        )
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        self.db = DatabaseManager(DATABASE_PATH)
        self.tree.on_error = self.on_app_command_error

    async def setup_hook(self):
        # Initialize Database
        await self.db.initialize()
        print(f"[KreeManager] Database initialized.")

        # Register Persistent Views
        from systems.views import PersistentRulesView, PersistentRoleView
        from config import PLAYER_ROLE_ID
        self.add_view(PersistentRulesView(PLAYER_ROLE_ID))
        self.add_view(PersistentRoleView())
        print(f"[KreeManager] Persistent views registered.")

        # Load Cogs
        for folder in ['commands', 'systems', 'events']:
            path = os.path.join(os.path.dirname(__file__), folder)
            if os.path.exists(path):
                for filename in os.listdir(path):
                    if filename.endswith(".py") and not filename.startswith("__"):
                        try:
                            await self.load_extension(f"{folder}.{filename[:-3]}")
                            print(f"Loaded {folder}.{filename[:-3]}")
                        except Exception as e:
                            print(f"Failed to load {folder}.{filename[:-3]}: {e}")

        # Sync Slash Commands
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash commands.")
        except Exception as e:
            print(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        print(f"[KreeManager] Logged in as {self.user} (ID: {self.user.id})")
        print(f"[KreeManager] Connected to the following servers:")
        for guild in self.guilds:
            print(f" - {guild.name} (ID: {guild.id})")
        print(f"[KreeManager] Bot is online and ready.")
        await self.change_presence(activity=discord.Game(name="Managing Esports Teams 🔥"))

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            print(f"[KreeManager] Component Interaction: {interaction.data.get('custom_id')} from {interaction.user}")
        await super().on_interaction(interaction)
        
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        print(f"[KreeManager] SLASH COMMAND ERROR: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ Command Error: {error}", ephemeral=True)

async def main():
    if not TOKEN or TOKEN == "your_token_here":
        print("ERROR: Discord Token not found. Please set it in KreeManager/.env")
        return
        
    bot = KreeManager()
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Fatal Error: {e}")
