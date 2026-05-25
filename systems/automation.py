import discord
from discord.ext import tasks, commands
import datetime
from config import BOT_NAME, ADMIN_ROLE_ID, COACH_ROLE_ID, EMBED_COLOR, ERROR_COLOR, SUCCESS_COLOR
import aiosqlite

class Automation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_checks.start()
        self.presence_check.start()
        self.evaluate_goals_loop.start()
        self.goal_reminders_loop.start()

    def cog_unload(self):
        self.weekly_checks.cancel()
        self.presence_check.cancel()
        self.evaluate_goals_loop.cancel()
        self.goal_reminders_loop.cancel()

    @tasks.loop(hours=24)
    async def presence_check(self):
        """Check for players who haven't been active in 48 hours"""
        inactive = await self.bot.db.get_inactive_players(days=2)
        for discord_id, ign in inactive:
            member = self.bot.get_user(discord_id)
            if member:
                try:
                    await member.send(f"👋 Hey **{ign}**, we haven't seen you active in the server for 48 hours. Is everything okay? Remember to use `/request_vacation` if you need a break!")
                except:
                    pass

    @tasks.loop(hours=168) # Weekly
    async def weekly_checks(self):
        """Handle Performance Promotions and Attendance Benchmarks"""
        players = await self.bot.db.get_all_players()
        
        report_channel_id = await self.bot.db.get_setting("announcement_channel")
        channel = self.bot.get_channel(int(report_channel_id)) if report_channel_id else None

        if not channel: return

        for p in players:
            d_id, ign = p[0], p[1]
            
            # 1. Performance Promotion Suggestion
            stats = await self.bot.db.get_player_stats(d_id)
            if stats and len(stats) >= 3: # Minimum 3 matches
                avg_rating = sum([(s[2]*2 + s[3] + s[5]*5 + s[6] + s[7] + s[8] - s[9]*3) for s in stats]) / len(stats)
                if avg_rating > 50:
                    embed = discord.Embed(title="⭐ Promotion Candidate", color=discord.Color.gold())
                    embed.description = f"**{ign}** has been performing exceptionally well this week."
                    embed.add_field(name="Avg Rating", value=f"{avg_rating:.1f}", inline=True)
                    embed.add_field(name="Matches", value=str(len(stats)), inline=True)
                    embed.set_footer(text="Staff, please review for Tier promotion.")
                    await channel.send(embed=embed)

    @tasks.loop(hours=1)
    async def evaluate_goals_loop(self):
        """Evaluate trial goals hourly, trigger failure logs, and check for roster restructure alerts"""
        # Call the evaluate_goals DB method
        expired_goals = await self.bot.db.evaluate_goals()
        
        for g_id, team_id, goal_text, team_name in expired_goals:
            # Log failure
            await self.bot.db.log_trial_action("GOAL_FAILED", f"Team {team_name} failed goal: {goal_text}")
            
            # Find trial team channel configuration to send alert
            db_team = await self.bot.db.get_trial_team(team_id=team_id)
            if db_team:
                category_id = db_team[8]
                guild = self.bot.guilds[0] if self.bot.guilds else None
                if guild and category_id:
                    category = guild.get_channel(category_id)
                    if category:
                        # Send alert to team announcements or team chat
                        target_chan = discord.utils.get(category.text_channels, name="announcements") or discord.utils.get(category.text_channels, name="team-chat")
                        if target_chan:
                            embed = discord.Embed(
                                title="🚨 Competitive Goal Failed",
                                color=ERROR_COLOR,
                                description=f"The team failed to complete the goal: **{goal_text}** before the deadline.\n\n⚠️ **Roster Restructure Review** has been initiated. Inactive or low-performing players may be rotated."
                            )
                            await target_chan.send(embed=embed)
            
            # Send notification to Staff Headquarters / Report Channel
            report_channel_id = await self.bot.db.get_setting("report_channel_id")
            if report_channel_id and report_channel_id != '0':
                staff_chan = self.bot.get_channel(int(report_channel_id))
                if staff_chan:
                    embed = discord.Embed(
                        title="🚨 Trial Team Goal Failure",
                        color=ERROR_COLOR,
                        description=f"**{team_name}** has failed their goal: *\"{goal_text}\"*."
                    )
                    embed.add_field(name="Auto-Action", value="Triggered roster restructuring review. Run `/restructure` to rebuild.")
                    await staff_chan.send(embed=embed)

    @tasks.loop(hours=24)
    async def goal_reminders_loop(self):
        """Send daily reminders for pending trial goals expiring soon"""
        all_teams = await self.bot.db.get_all_trial_teams()
        guild = self.bot.guilds[0] if self.bot.guilds else None
        if not guild:
            return

        for team in all_teams:
            team_id = team[0]
            team_name = team[1]
            category_id = team[8]
            
            goals = await self.bot.db.get_team_goals(team_id)
            pending_goals = [g for g in goals if g[6] == 'Pending']
            
            if not pending_goals:
                continue

            # Check if category exists
            category = guild.get_channel(category_id)
            if not category:
                continue

            target_chan = discord.utils.get(category.text_channels, name="team-chat") or discord.utils.get(category.text_channels, name="announcements")
            if not target_chan:
                continue

            for g in pending_goals:
                deadline_str = g[5]
                try:
                    deadline_dt = datetime.datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')
                    time_left = deadline_dt - datetime.datetime.now()
                    
                    if 0 < time_left.total_seconds() <= 86400: # Expiring in less than 24h
                        embed = discord.Embed(
                            title="⏳ Goal Deadline Impending",
                            color=discord.Color.orange(),
                            description=f"Goal: **{g[2]}**\nTarget: **{g[3]}**\nCurrent: **{g[4]}**\nTime Left: **{time_left.seconds // 3600} hours**!"
                        )
                        embed.set_footer(text="Complete this goal to avoid roster restructure review!")
                        await target_chan.send(embed=embed)
                except Exception as e:
                    print(f"[KreeManager] Error parsing deadline for goal {g[0]}: {e}")

    @presence_check.before_loop
    @weekly_checks.before_loop
    @evaluate_goals_loop.before_loop
    @goal_reminders_loop.before_loop
    async def before_checks(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Automation(bot))
