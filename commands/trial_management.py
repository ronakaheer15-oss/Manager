import discord
from discord import app_commands
from discord.ext import commands
import datetime
import aiosqlite
from config import EMBED_COLOR, SUCCESS_COLOR, ERROR_COLOR
from utils.checks import is_staff, is_manager, is_admin

class TrialManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="assign", description="Manually assign a player to a team and role")
    @app_commands.describe(member="The player to assign", team_name="Name of the team (e.g. Trial Team 1)", role_type="Role (Captain, Manager, Coach, Analyst, Player)")
    @is_staff()
    async def assign(self, interaction: discord.Interaction, member: discord.Member, team_name: str, role_type: str):
        await interaction.response.defer()
        guild = interaction.guild

        # 1. Fetch Trial Team details from DB
        db_team = await self.bot.db.get_trial_team(name=team_name)
        if not db_team:
            await interaction.followup.send(f"❌ Team **{team_name}** not found in database. Run `/setup_server` or create the team first.", ephemeral=True)
            return

        team_id = db_team[0]
        role_map = {
            "captain": db_team[3],
            "manager": db_team[4],
            "coach": db_team[5],
            "analyst": db_team[6],
            "player": db_team[7]
        }

        role_key = role_type.lower()
        if role_key not in role_map:
            await interaction.followup.send("❌ Invalid role type. Choose from: Captain, Manager, Coach, Analyst, Player.", ephemeral=True)
            return

        target_role_id = role_map[role_key]
        target_role = guild.get_role(target_role_id)
        team_role = guild.get_role(db_team[2])

        if not target_role or not team_role:
            await interaction.followup.send("❌ Discord roles for this team are missing. Rebuilding team roles is required.", ephemeral=True)
            return

        # 2. Make sure player profile exists
        player_profile = await self.bot.db.get_player(member.id)
        if not player_profile:
            await self.bot.db.create_player(member.id, member.display_name)

        # 3. Update database
        await self.bot.db.update_player(
            member.id,
            team_id=team_id,
            role=role_type.capitalize(),
            tier="Trial",
            verification_status="Verified"
        )

        # 4. Update discord roles (Remove previous trial roles of this team first)
        try:
            # Gather all roles of this trial team to clean up first
            all_team_roles = [guild.get_role(rid) for rid in role_map.values() if rid]
            await member.remove_roles(*[r for r in all_team_roles if r in member.roles])
            
            # Add new roles
            await member.add_roles(team_role, target_role, reason=f"Manual assign to {team_name} as {role_type}")
        except Exception as e:
            await interaction.followup.send(f"⚠️ Assigned in DB, but failed to update Discord roles: {e}")
            return

        # 5. Log and notify
        await self.bot.db.log_trial_action("ASSIGN", f"Assigned {member} to {team_name} as {role_type}.")
        
        embed = discord.Embed(title="📋 Team Roster Update", color=SUCCESS_COLOR)
        embed.description = f"Successfully assigned {member.mention} to **{team_name}** as **{role_type.capitalize()}**."
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="promote", description="Manually approve trial team promotion to permanent roster")
    @app_commands.describe(team_name="Name of the Trial Team (e.g. Trial Team 1)", permanent_team_name="Name for the new permanent roster")
    @is_staff()
    async def promote_team(self, interaction: discord.Interaction, team_name: str, permanent_team_name: str):
        await interaction.response.defer()
        guild = interaction.guild

        # 1. Fetch Trial Team details from DB
        db_team = await self.bot.db.get_trial_team(name=team_name)
        if not db_team:
            await interaction.followup.send(f"❌ Trial team **{team_name}** not found.", ephemeral=True)
            return

        team_id = db_team[0]
        category_id = db_team[8]

        # 2. Create new permanent team in database
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            await db.execute("INSERT INTO teams (name, tier) VALUES (?, 'Tier 3')", (permanent_team_name,))
            async with db.execute("SELECT id FROM teams WHERE name = ?", (permanent_team_name,)) as cursor:
                row = await cursor.fetchone()
                perm_team_id = row[0] if row else None
            await db.commit()

        if not perm_team_id:
            await interaction.followup.send("❌ Failed to create permanent team in DB.", ephemeral=True)
            return

        # 3. Create permanent Role
        perm_role = await guild.create_role(name=permanent_team_name, reason="Trial Promotion")

        # 4. Reorganize/Archive Category and Channels
        category = guild.get_channel(category_id)
        if category:
            try:
                await category.edit(name=f"🏢 {permanent_team_name.upper()}")
                # Reset category permission overrides for permanent team
                await category.set_permissions(guild.default_role, overwrite=discord.PermissionOverwrite(view_channel=False))
                await category.set_permissions(perm_role, overwrite=discord.PermissionOverwrite(view_channel=True))
                
                # Archive Trial roles
                trial_role = guild.get_role(db_team[2])
                if trial_role:
                    await category.set_permissions(trial_role, overwrite=None)
            except Exception as e:
                print(f"[KreeManager] Warning during category re-perm: {e}")

        # 5. Move all players from Trial Team to Permanent Team
        players = await self.bot.db.get_trial_team_players(team_id)
        for p in players:
            discord_id = p[0]
            member = guild.get_member(discord_id)
            if member:
                try:
                    await member.add_roles(perm_role)
                    # Clean up old trial roles
                    trial_roles = [guild.get_role(db_team[i]) for i in range(2, 8) if db_team[i]]
                    await member.remove_roles(*[r for r in trial_roles if r in member.roles])
                except Exception as e:
                    print(f"[KreeManager] Error updating roles for {member}: {e}")

            # Update DB Player profile
            await self.bot.db.update_player(
                discord_id,
                team_id=perm_team_id,
                tier="Tier 3",
                verification_status="Verified"
            )

        # 6. Delete/Archive old trial team database records & Roles
        await self.bot.db.delete_trial_team(team_id)
        try:
            trial_role = guild.get_role(db_team[2])
            if trial_role:
                await trial_role.delete()
        except:
            pass

        # 7. Announce the promotion
        announcement_chan = None
        report_channel_id = await self.bot.db.get_setting("announcement_channel")
        if report_channel_id:
            announcement_chan = guild.get_channel(int(report_channel_id))
        if not announcement_chan:
            for chan in guild.text_channels:
                if "announcement" in chan.name.lower():
                    announcement_chan = chan
                    break

        embed = discord.Embed(title="🎉 ORGANIZATION PROMOTION", color=discord.Color.gold())
        embed.description = (
            f"Please join us in celebrating the promotion of **{team_name}** to our permanent roster!\n\n"
            f"🛡️ **Official Team Name:** {permanent_team_name}\n"
            f"📈 **Roster Status:** Tier 3 Division\n"
            f"👥 **Roster Size:** {len(players)} Players\n\n"
            f"They have successfully passed all trial milestones and demonstrated championship excellence! 🏆"
        )
        embed.set_footer(text="Kree Esports Pathway Program")
        
        if announcement_chan:
            await announcement_chan.send(embed=embed)
        await interaction.followup.send(embed=embed)
        await self.bot.db.log_trial_action("PROMOTION", f"Promoted {team_name} to permanent team {permanent_team_name}.")

    @app_commands.command(name="restructure", description="Trigger dynamic roster rotation/rebuild for a team")
    @app_commands.describe(team_name="Name of the team (e.g. Trial Team 1)")
    @is_manager()
    async def restructure_team(self, interaction: discord.Interaction, team_name: str):
        await interaction.response.defer()
        guild = interaction.guild

        # 1. Fetch Trial Team details from DB
        db_team = await self.bot.db.get_trial_team(name=team_name)
        if not db_team:
            await interaction.followup.send(f"❌ Team **{team_name}** not found.", ephemeral=True)
            return

        team_id = db_team[0]
        players = await self.bot.db.get_trial_team_players(team_id)

        # 2. Identify inactive or low-discipline players
        inactive_players = []
        active_players = []
        for p in players:
            d_id = p[0]
            ign = p[1]
            last_seen_str = p[16]
            discipline_score = p[19]
            reliability_score = p[20]
            
            # Simple metric: inactive if last seen > 3 days, or reliability < 70
            is_inactive = False
            try:
                last_seen_dt = datetime.datetime.strptime(last_seen_str, '%Y-%m-%d %H:%M:%S')
                if (datetime.datetime.now() - last_seen_dt).days >= 3:
                    is_inactive = True
            except:
                pass
            
            if reliability_score < 70 or discipline_score < 60:
                is_inactive = True

            if is_inactive:
                inactive_players.append(p)
            else:
                active_players.append(p)

        if not inactive_players:
            await interaction.followup.send(f"✅ Team **{team_name}** is fully active and compliant. No restructure required.", ephemeral=True)
            return

        # 3. Find Free Agents / Unassigned players
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            async with db.execute("SELECT * FROM players WHERE team_id IS NULL AND status = 'Active' ORDER BY last_seen DESC LIMIT 5") as cursor:
                free_agents = await cursor.fetchall()

        swaps = []
        # 4. Perform Swaps
        for i, inactive_player in enumerate(inactive_players):
            if i >= len(free_agents):
                break
            replacement = free_agents[i]
            
            # Rotate out inactive
            await self.bot.db.update_player(inactive_player[0], team_id=None, tier="Reserve")
            member_out = guild.get_member(inactive_player[0])
            if member_out:
                try:
                    trial_roles = [guild.get_role(db_team[j]) for j in range(2, 8) if db_team[j]]
                    await member_out.remove_roles(*[r for r in trial_roles if r in member_out.roles])
                except:
                    pass

            # Rotate in active replacement
            await self.bot.db.update_player(replacement[0], team_id=team_id, tier="Trial", role="Player")
            member_in = guild.get_member(replacement[0])
            if member_in:
                try:
                    team_role = guild.get_role(db_team[2])
                    player_role = guild.get_role(db_team[7])
                    await member_in.add_roles(team_role, player_role)
                except:
                    pass

            swaps.append((inactive_player[1], replacement[1]))

        if not swaps:
            await interaction.followup.send(f"⚠️ Restructure needed for **{team_name}**, but no active free agents are available to swap.", ephemeral=True)
            return

        # 5. Log and Announce swaps
        swap_desc = "\n".join([f"🔄 Rotated Out: **{out_n}** ➡️ Rotated In: **{in_n}**" for out_n, in_n in swaps])
        await self.bot.db.log_trial_action("RESTRUCTURE", f"Restructured {team_name}. Swaps: {swaps}")

        # Send alert to team channels
        category = guild.get_channel(category_id)
        if category:
            team_chat = discord.utils.get(category.text_channels, name="team-chat")
            if team_chat:
                embed = discord.Embed(title="🔄 Roster Restructure Alert", color=ERROR_COLOR)
                embed.description = f"Management has triggered a roster restructure for **{team_name}** due to inactivity/performance metrics.\n\n{swap_desc}"
                await team_chat.send(embed=embed)

        embed = discord.Embed(title="🛠️ Roster Rebuild Execution", color=SUCCESS_COLOR)
        embed.description = f"Roster restructured for **{team_name}** successfully.\n\n{swap_desc}"
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="setgoal", description="Assign a competitive performance goal to a trial team")
    @app_commands.describe(team_name="Name of the team (e.g. Trial Team 1)", goal_text="Description of the goal", target_value="Target metric (e.g. wins count, days count)", deadline_days="Days to complete the goal")
    @is_manager()
    async def set_goal(self, interaction: discord.Interaction, team_name: str, goal_text: str, target_value: int, deadline_days: int):
        await interaction.response.defer()
        guild = interaction.guild

        # 1. Fetch Trial Team details from DB
        db_team = await self.bot.db.get_trial_team(name=team_name)
        if not db_team:
            await interaction.followup.send(f"❌ Team **{team_name}** not found.", ephemeral=True)
            return

        team_id = db_team[0]
        category_id = db_team[8]

        # 2. Add goal to database
        goal_id = await self.bot.db.add_trial_goal(team_id, goal_text, target_value, deadline_days)
        
        # 3. Post Goal Announcement in team category
        category = guild.get_channel(category_id)
        if category:
            announcements = discord.utils.get(category.text_channels, name="announcements") or discord.utils.get(category.text_channels, name="team-chat")
            if announcements:
                embed = discord.Embed(title="🎯 NEW COMPETITIVE GOAL ASSIGNED", color=EMBED_COLOR)
                embed.description = f"Your team has been assigned a new milestone objective!"
                embed.add_field(name="Goal", value=goal_text, inline=False)
                embed.add_field(name="Target Value", value=f"**{target_value}**", inline=True)
                embed.add_field(name="Deadline", value=f"🕒 **{deadline_days} Days**", inline=True)
                embed.set_footer(text="Progress will be monitored automatically.")
                await announcements.send(embed=embed)

        await self.bot.db.log_trial_action("SET_GOAL", f"Set goal for {team_name}: {goal_text} (Target: {target_value}, Days: {deadline_days})")
        await interaction.followup.send(f"✅ Goal successfully set for **{team_name}**!")

    @app_commands.command(name="removeplayer", description="Remove an inactive player from their trial team")
    @app_commands.describe(member="The player to remove")
    @is_manager()
    async def remove_player(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer()
        guild = interaction.guild

        # 1. Fetch player details
        player = await self.bot.db.get_player(member.id)
        if not player or not player[17]:
            await interaction.followup.send(f"❌ {member.display_name} is not assigned to any trial team.", ephemeral=True)
            return

        team_id = player[17]
        db_team = await self.bot.db.get_trial_team(team_id=team_id)
        if not db_team:
            await interaction.followup.send("❌ Trial team details not found.", ephemeral=True)
            return

        team_name = db_team[1]

        # 2. Update DB
        await self.bot.db.update_player(member.id, team_id=None, tier="Reserve")

        # 3. Update Discord Roles
        try:
            trial_roles = [guild.get_role(db_team[i]) for i in range(2, 8) if db_team[i]]
            await member.remove_roles(*[r for r in trial_roles if r in member.roles])
        except Exception as e:
            print(f"[KreeManager] Error removing trial roles: {e}")

        # 4. Notify & Log
        category = guild.get_channel(db_team[8])
        if category:
            team_chat = discord.utils.get(category.text_channels, name="team-chat")
            if team_chat:
                await team_chat.send(f"🚪 **{member.display_name}** has been removed from the roster.")

        await self.bot.db.log_trial_action("REMOVE_PLAYER", f"Removed {member} from {team_name}.")
        await interaction.followup.send(f"✅ Removed {member.mention} from **{team_name}** and shifted them to reserves.")

    @app_commands.command(name="teamreport", description="Generate team analytics and compliance summary")
    @app_commands.describe(team_name="Name of the team (e.g. Trial Team 1)")
    async def team_report(self, interaction: discord.Interaction, team_name: str):
        await interaction.response.defer()
        
        # 1. Fetch team details
        db_team = await self.bot.db.get_trial_team(name=team_name)
        if not db_team:
            await interaction.followup.send(f"❌ Team **{team_name}** not found.", ephemeral=True)
            return

        team_id = db_team[0]
        players = await self.bot.db.get_trial_team_players(team_id)

        # 2. Roster Details
        roster_text = ""
        total_attendance = 0
        total_discipline = 0
        for p in players:
            ign = p[1]
            role = p[3] or "Player"
            attendance_score = p[20] # reliability
            discipline_score = p[19]
            total_attendance += attendance_score
            total_discipline += discipline_score
            roster_text += f"• **{ign}** ({role}) - Reliability: `{attendance_score}%` | Discipline: `{discipline_score}`\n"

        avg_attendance = (total_attendance / len(players)) if players else 0
        avg_discipline = (total_discipline / len(players)) if players else 0

        # 3. Goals Progress details
        goals = await self.bot.db.get_team_goals(team_id)
        goals_text = ""
        completed_goals = 0
        for g in goals:
            status_emoji = "✅" if g[6] == 'Completed' else "❌" if g[6] == 'Failed' else "⏳"
            goals_text += f"{status_emoji} *{g[2]}* - Progress: `{g[4]}/{g[3]}` (Status: {g[6]})\n"
            if g[6] == 'Completed':
                completed_goals += 1

        goal_rate = (completed_goals / len(goals) * 100) if goals else 0

        # 4. Build report embed
        embed = discord.Embed(title=f"📊 PERFORMANCE REPORT: {team_name}", color=EMBED_COLOR)
        embed.description = f"Esports analytics for **{team_name}** competitive division."
        
        embed.add_field(name="👥 Active Roster", value=roster_text if roster_text else "No players assigned.", inline=False)
        embed.add_field(name="📈 Metrics", value=f"• Avg Attendance: `{avg_attendance:.1f}%` \n• Avg Discipline: `{avg_discipline:.1f}/100` \n• Scrim Win Rate: `TBD` (Link to Scrim system)", inline=True)
        embed.add_field(name="🎯 Milestones & Goals", value=goals_text if goals_text else "No competitive goals set.", inline=False)
        embed.add_field(name="Completion Rate", value=f"**{goal_rate:.1f}%**", inline=True)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="override", description="Override database records or team automation values (Admin Only)")
    @app_commands.describe(member="Select player to override", discipline_score="New discipline score", reliability_score="New reliability score")
    @is_admin()
    async def admin_override(self, interaction: discord.Interaction, member: discord.Member, discipline_score: int = None, reliability_score: int = None):
        await interaction.response.defer(ephemeral=True)

        player = await self.bot.db.get_player(member.id)
        if not player:
            await interaction.followup.send("❌ Player profile not found.", ephemeral=True)
            return

        updates = {}
        if discipline_score is not None:
            updates['discipline_score'] = min(100, max(0, discipline_score))
        if reliability_score is not None:
            updates['reliability_score'] = min(100, max(0, reliability_score))

        if not updates:
            await interaction.followup.send("❌ Nothing specified to update.", ephemeral=True)
            return

        await self.bot.db.update_player(member.id, **updates)
        await self.bot.db.log_trial_action("OVERRIDE", f"Override settings applied for player {member} (ID: {member.id}): {updates}")
        
        await interaction.followup.send(f"✅ Override applied successfully for {member.display_name}: {updates}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TrialManagement(bot))
