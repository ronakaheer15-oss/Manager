import discord
from discord.ext import commands
import re
import asyncio

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))

class TrialTeamEngine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Lock to prevent concurrent onboarding race conditions
        self.lock = asyncio.Lock()

    def normalize(self, text):
        return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

    async def get_or_create_trial_role(self, guild, name):
        # Scan for existing role to prevent duplication
        role = discord.utils.get(guild.roles, name=name)
        if not role:
            role = await guild.create_role(name=name, reason=f"KreeManager Dynamic Trial Role: {name}")
            safe_print(f"[KreeManager] Created role: {name}")
        return role

    async def get_or_create_trial_team(self, guild, team_index):
        category_name = f"🏆 TRIAL TEAM {team_index}"
        normalized_cat = self.normalize(category_name)
        
        # 1. Category Smart Detection
        category = None
        for cat in guild.categories:
            if self.normalize(cat.name) == normalized_cat:
                category = cat
                safe_print(f"[KreeManager] Reusing category: {category.name}")
                break
        
        # 2. Role Smart Detection / Creation
        role_main = await self.get_or_create_trial_role(guild, f"Trial Team {team_index}")
        role_captain = await self.get_or_create_trial_role(guild, f"Captain (Trial {team_index})")
        role_manager = await self.get_or_create_trial_role(guild, f"Manager (Trial {team_index})")
        role_coach = await self.get_or_create_trial_role(guild, f"Coach (Trial {team_index})")
        role_analyst = await self.get_or_create_trial_role(guild, f"Analyst (Trial {team_index})")
        role_player = await self.get_or_create_trial_role(guild, f"Player (Trial {team_index})")

        # 3. Create category if not found
        if not category:
            # Setup initial permissions
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                role_main: discord.PermissionOverwrite(view_channel=True),
                role_manager: discord.PermissionOverwrite(view_channel=True, manage_messages=True, mention_everyone=True),
                role_captain: discord.PermissionOverwrite(view_channel=True, mention_everyone=True),
                role_coach: discord.PermissionOverwrite(view_channel=True),
                role_analyst: discord.PermissionOverwrite(view_channel=True),
                role_player: discord.PermissionOverwrite(view_channel=True)
            }
            category = await guild.create_category(category_name, overwrites=overwrites)
            safe_print(f"[KreeManager] Created category: {category_name}")
        else:
            # Sync permissions to existing category if needed
            try:
                await category.set_permissions(guild.default_role, overwrite=discord.PermissionOverwrite(view_channel=False))
                await category.set_permissions(role_main, overwrite=discord.PermissionOverwrite(view_channel=True))
                await category.set_permissions(role_manager, overwrite=discord.PermissionOverwrite(view_channel=True, manage_messages=True, mention_everyone=True))
                await category.set_permissions(role_captain, overwrite=discord.PermissionOverwrite(view_channel=True, mention_everyone=True))
                await category.set_permissions(role_coach, overwrite=discord.PermissionOverwrite(view_channel=True))
                await category.set_permissions(role_analyst, overwrite=discord.PermissionOverwrite(view_channel=True))
                await category.set_permissions(role_player, overwrite=discord.PermissionOverwrite(view_channel=True))
            except Exception as e:
                print(f"[KreeManager] Warning: failed to set category permissions: {e}")

        # 4. Channel Provisioning
        channels_to_create = ["team-chat", "scrim-chat", "strategy-room", "announcements", "attendance-log"]
        created_channels = {}
        
        for chan_name in channels_to_create:
            normalized_chan = self.normalize(chan_name)
            channel = None
            
            # Smart check existing channels in category
            for chan in category.text_channels:
                if self.normalize(chan.name) == normalized_chan:
                    channel = chan
                    safe_print(f"[KreeManager] Reusing channel: #{chan.name} in category {category.name}")
                    break
            
            if not channel:
                channel = await guild.create_text_channel(chan_name, category=category)
                safe_print(f"[KreeManager] Created channel: #{chan_name} in category {category.name}")
            
            created_channels[chan_name] = channel.id

        # 5. DB Persistence
        db_team = await self.bot.db.get_trial_team(name=f"Trial Team {team_index}")
        if not db_team:
            team_id = await self.bot.db.create_trial_team(
                name=f"Trial Team {team_index}",
                role_id=role_main.id,
                captain_role_id=role_captain.id,
                manager_role_id=role_manager.id,
                coach_role_id=role_coach.id,
                analyst_role_id=role_analyst.id,
                player_role_id=role_player.id,
                category_id=category.id
            )
            safe_print(f"[KreeManager] Created Trial Team {team_index} record in DB.")
            await self.bot.db.log_trial_action("TEAM_CREATION", f"Trial Team {team_index} created.")
        else:
            team_id = db_team[0]

        return team_id, role_main, role_player, category

    async def assign_player_to_trial_team(self, member):
        async with self.lock:
            guild = member.guild
            safe_print(f"[KreeManager] Assigning {member} to a trial team.")

            # Make sure player profile exists
            player_profile = await self.bot.db.get_player(member.id)
            if not player_profile:
                # Set up initial profile
                await self.bot.db.create_player(member.id, member.display_name)
                player_profile = await self.bot.db.get_player(member.id)

            # Check if player is already assigned to a trial team
            current_team_id = player_profile[17] if player_profile else None
            if current_team_id:
                db_team = await self.bot.db.get_trial_team(team_id=current_team_id)
                if db_team:
                    safe_print(f"[KreeManager] Player {member} is already in {db_team[1]}")
                    return db_team[1]

            # Find or Create a Trial Team with space (< 5 players)
            all_teams = await self.bot.db.get_all_trial_teams()
            target_team_id = None
            target_team_name = ""
            role_main = None
            role_player = None

            for team in all_teams:
                team_id = team[0]
                team_name = team[1]
                players = await self.bot.db.get_trial_team_players(team_id)
                if len(players) < 5:
                    # Target team found!
                    target_team_id = team_id
                    target_team_name = team_name
                    role_main = guild.get_role(team[2])
                    role_player = guild.get_role(team[7])
                    break

            if not target_team_id:
                # No space in existing teams or no teams exist, create a new one!
                new_index = len(all_teams) + 1
                target_team_id, role_main, role_player, category = await self.get_or_create_trial_team(guild, new_index)
                target_team_name = f"Trial Team {new_index}"

            # If roles are missing (e.g. deleted from guild), restore them
            if not role_main or not role_player:
                # Re-fetch or create roles
                team_idx = int(target_team_name.split(" ")[-1])
                _, role_main, role_player, _ = await self.get_or_create_trial_team(guild, team_idx)

            # Assign Player to Team in DB
            await self.bot.db.update_player(
                member.id,
                team_id=target_team_id,
                tier="Trial",
                verification_status="Verified"
            )

            # Assign Discord Roles
            try:
                roles_to_add = [role_main, role_player]
                # Also assign starter Player role from config if it exists
                from config import PLAYER_ROLE_ID
                starter_role = guild.get_role(PLAYER_ROLE_ID)
                if starter_role:
                    roles_to_add.append(starter_role)
                
                await member.add_roles(*roles_to_add, reason="Trial Team Onboarding")
                safe_print(f"[KreeManager] Assigned trial roles to {member}")
            except Exception as e:
                safe_print(f"[KreeManager] Error assigning roles to {member}: {e}")

            # Send welcome message in `#team-chat` channel
            db_team_details = await self.bot.db.get_trial_team(team_id=target_team_id)
            category_id = db_team_details[8] if db_team_details else None
            if category_id:
                category = guild.get_channel(category_id)
                if category:
                    team_chat = discord.utils.get(category.text_channels, name="team-chat")
                    if team_chat:
                        embed = discord.Embed(
                            title=f"🆕 New Recruit: {member.display_name}",
                            color=discord.Color.blue()
                        )
                        embed.description = (
                            f"Welcome {member.mention} to **{target_team_name}**!\n\n"
                            "🏆 **Onboarding Checklist:**\n"
                            "1. Sync schedules in `#scrim-chat`.\n"
                            "2. View strategies in `#strategy-room`.\n"
                            "3. Keep track of announcements and sign attendance in `#attendance-log`.\n\n"
                            "Good luck with your trial journey! 🔥"
                        )
                        embed.set_thumbnail(url=member.display_avatar.url)
                        await team_chat.send(content=f"{member.mention}", embed=embed)

            # Log Trial Action
            await self.bot.db.log_trial_action("PLAYER_ASSIGNMENT", f"Player {member} (ID: {member.id}) assigned to {target_team_name}.")
            return target_team_name

async def setup(bot):
    await bot.add_cog(TrialTeamEngine(bot))
