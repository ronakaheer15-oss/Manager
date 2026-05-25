import discord
from discord import app_commands
from config import ADMIN_ROLE_ID, COACH_ROLE_ID, PLAYER_ROLE_ID, TEAM_MANAGER_ROLE_ID, STAFF_ROLE_ID

def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        return any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles) or interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

def is_manager():
    async def predicate(interaction: discord.Interaction) -> bool:
        return any(role.id in [ADMIN_ROLE_ID, TEAM_MANAGER_ROLE_ID] for role in interaction.user.roles) or interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

def is_staff():
    async def predicate(interaction: discord.Interaction) -> bool:
        return any(role.id in [ADMIN_ROLE_ID, COACH_ROLE_ID, TEAM_MANAGER_ROLE_ID, STAFF_ROLE_ID] for role in interaction.user.roles) or interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

def is_player():
    async def predicate(interaction: discord.Interaction) -> bool:
        return any(role.id in [ADMIN_ROLE_ID, COACH_ROLE_ID, TEAM_MANAGER_ROLE_ID, STAFF_ROLE_ID, PLAYER_ROLE_ID] for role in interaction.user.roles) or interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

