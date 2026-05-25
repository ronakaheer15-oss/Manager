import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
from config import EMBED_COLOR
from utils.checks import is_staff, is_manager

class TeamManagement(commands.GroupCog, name="teams"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="filter", description="Filter teams by tier")
    @app_commands.describe(tier="The tier to filter by (e.g., T1, T2)")
    async def filter_teams(self, interaction: discord.Interaction, tier: str):
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            async with db.execute("SELECT name, manager_id FROM teams WHERE tier = ?", (tier,)) as cursor:
                teams = await cursor.fetchall()
        
        if not teams:
            await interaction.response.send_message(f"No teams found in tier **{tier}**.", ephemeral=True)
            return
            
        embed = discord.Embed(title=f"🏢 {tier} Teams", color=EMBED_COLOR)
        for t in teams:
            manager = f"<@{t[1]}>" if t[1] else "Unassigned"
            embed.add_field(name=t[0], value=f"Manager: {manager}", inline=False)
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="inactive", description="View all currently inactive players across all teams")
    @is_staff()
    async def inactive_players(self, interaction: discord.Interaction, days: int = 3):
        inactive = await self.bot.db.get_inactive_players(days)
        if not inactive:
            await interaction.response.send_message(f"✅ All players have been active within the last {days} days.", ephemeral=True)
            return

        embed = discord.Embed(title=f"🚨 Inactive Players (Last {days} days)", color=discord.Color.red())
        for discord_id, ign in inactive:
            embed.add_field(name=ign, value=f"<@{discord_id}>", inline=True)
            
        await interaction.response.send_message(embed=embed)

class Team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="promote_player", description="Promote a player to a higher tier")
    @is_staff()
    async def promote_player_cmd(self, interaction: discord.Interaction, member: discord.Member, tier: str):
        player = await self.bot.db.get_player(member.id)
        if not player:
            await interaction.response.send_message(f"❌ {member.display_name} doesn't have a profile yet.", ephemeral=True)
            return

        await self.bot.db.update_player(member.id, tier=tier)
        await interaction.response.send_message(f"✅ {member.mention} has been promoted to **{tier}**!")

    @app_commands.command(name="demote", description="Demote a player to a lower tier")
    @is_staff()
    async def demote(self, interaction: discord.Interaction, member: discord.Member, tier: str):
        player = await self.bot.db.get_player(member.id)
        if not player:
            await interaction.response.send_message(f"❌ {member.display_name} doesn't have a profile yet.", ephemeral=True)
            return

        await self.bot.db.update_player(member.id, tier=tier)
        await interaction.response.send_message(f"⚠️ {member.mention} has been demoted to **{tier}**.")

    @app_commands.command(name="assignrole", description="Assign an esports role to a player")
    @is_staff()
    async def assignrole(self, interaction: discord.Interaction, member: discord.Member, role: str):
        player = await self.bot.db.get_player(member.id)
        if not player:
            await interaction.response.send_message(f"❌ {member.display_name} doesn't have a profile yet.", ephemeral=True)
            return

        await self.bot.db.update_player(member.id, role=role)
        await interaction.response.send_message(f"✅ {member.mention}'s role has been updated to **{role}**.")

    @app_commands.command(name="team", description="View the team roster grouped by team and tier with Win Rate")
    async def team(self, interaction: discord.Interaction):
        players = await self.bot.db.get_all_players()
        
        if not players:
            await interaction.response.send_message("No players found in the database.", ephemeral=True)
            return

        # Fetch teams and map_stats
        team_map = {None: "Unassigned/Free Agents"}
        team_winrates = {}
        
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            async with db.execute("SELECT id, name FROM teams") as cursor:
                teams = await cursor.fetchall()
                for t in teams:
                    team_map[t[0]] = t[1]
            
            # Calculate winrate for each team
            async with db.execute("SELECT team_id, result FROM map_stats") as cursor:
                all_stats = await cursor.fetchall()
                stats_calc = {}
                for tid, res in all_stats:
                    if tid not in stats_calc: stats_calc[tid] = {"wins": 0, "total": 0}
                    stats_calc[tid]["total"] += 1
                    if res == "Win": stats_calc[tid]["wins"] += 1
                
                for tid, s in stats_calc.items():
                    team_winrates[tid] = (s["wins"] / s["total"]) * 100

        roster = {}
        for p in players:
            team_id = p[17] if len(p) > 17 else None
            team_name = team_map.get(team_id, "Unknown Team")
            tier = p[11] or "Unranked"
            
            if team_name not in roster:
                roster[team_name] = {"tiers": {}, "id": team_id}
            if tier not in roster[team_name]["tiers"]:
                roster[team_name]["tiers"][tier] = []
                
            roster[team_name]["tiers"][tier].append(f"{p[1]} ({p[3] or 'N/A'})")

        embed = discord.Embed(title="🏢 Kree Esports Organization Roster", color=EMBED_COLOR)
        
        for t_name, data in roster.items():
            wr = team_winrates.get(data["id"], 0)
            team_info = f"📊 **Win Rate:** {wr:.1f}%\n"
            for tier, members in data["tiers"].items():
                team_info += f"**{tier}**\n" + "\n".join([f"• {m}" for m in members]) + "\n\n"
            
            embed.add_field(name=f"🛡️ {t_name}", value=team_info, inline=False)
            
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(TeamManagement(bot))
    await bot.add_cog(Team(bot))
