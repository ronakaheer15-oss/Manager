import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import asyncio
from config import EMBED_COLOR, SUCCESS_COLOR
import re
from systems.views import PersistentRulesView, PersistentRoleView

class SetupView(discord.ui.View):
    def __init__(self, bot, interaction):
        super().__init__(timeout=300)
        self.bot = bot
        self.interaction = interaction
        self.mode = "competitive"
        self.team_count = 1
        self.academy = False
        self.reused_count = 0
        self.created_count = 0
        
    async def update_message(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        status = f"✅ Mode: **{self.mode.capitalize()}**\n✅ Teams: **{self.team_count}**\n✅ Academy: **{'ON' if self.academy else 'OFF'}**"
        embed.set_field_at(0, name="Current Settings", value=status, inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.select(
        placeholder="Choose Organization Mode",
        options=[
            discord.SelectOption(label="Competitive", value="competitive", description="Strict permissions, scrim focus.", emoji="🏆"),
            discord.SelectOption(label="Casual/Community", value="casual", description="More public channels, relaxed rules.", emoji="💬")
        ]
    )
    async def select_mode(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.mode = select.values[0]
        await self.update_message(interaction)

    @discord.ui.select(
        placeholder="Team Count",
        options=[
            discord.SelectOption(label="1 Team", value="1"),
            discord.SelectOption(label="2 Teams", value="2"),
            discord.SelectOption(label="4 Teams", value="4"),
            discord.SelectOption(label="8 Teams", value="8")
        ]
    )
    async def select_teams(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.team_count = int(select.values[0])
        await self.update_message(interaction)

    @discord.ui.button(label="Toggle Academy (OFF)", style=discord.ButtonStyle.secondary)
    async def toggle_academy(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.academy = not self.academy
        button.label = f"Toggle Academy ({'ON' if self.academy else 'OFF'})"
        button.style = discord.ButtonStyle.success if self.academy else discord.ButtonStyle.secondary
        await self.update_message(interaction)

    @discord.ui.button(label="🚀 START SMART DEPLOYMENT", style=discord.ButtonStyle.primary, row=3)
    async def start_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="⛓️ **Initializing Professional Merge & Cleanup Engine...**", view=None, embed=None)
        await self.perform_setup(interaction)

    def normalize(self, text):
        return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

    async def perform_setup(self, interaction):
        guild = interaction.guild
        self.reused_count = 0
        self.created_count = 0

        # --- PHASE 1: MERGE & CLEANUP ---
        cats_by_norm = {}
        for cat in guild.categories:
            norm = self.normalize(cat.name)
            if norm not in cats_by_norm: cats_by_norm[norm] = []
            cats_by_norm[norm].append(cat)
        
        for norm, cats in cats_by_norm.items():
            if len(cats) > 1:
                primary = cats[0]
                for extra in cats[1:]:
                    for chan in extra.channels:
                        await chan.edit(category=primary)
                    await extra.delete()
                    self.reused_count += 1

        chans_by_norm = {}
        for chan in guild.channels:
            if isinstance(chan, (discord.TextChannel, discord.VoiceChannel)):
                norm = self.normalize(chan.name)
                ctype = type(chan)
                key = (norm, ctype)
                if key not in chans_by_norm: chans_by_norm[key] = []
                chans_by_norm[key].append(chan)
        
        for key, chans in chans_by_norm.items():
            if len(chans) > 1:
                for extra in chans[1:]:
                    await extra.delete()
                    self.reused_count += 1

        # --- PHASE 2: STRUCTURE DEPLOYMENT ---
        from config import (
            OWNER_ROLE_ID, ADMIN_ROLE_ID, TEAM_MANAGER_ROLE_ID, COACH_ROLE_ID,
            ANALYST_ROLE_ID, IGL_ROLE_ID, MODERATOR_ROLE_ID, MAIN_TEAM_ROLE_ID,
            PLAYER_ROLE_ID
        )
        
        role_map = {
            "Owner": OWNER_ROLE_ID, "Admin": ADMIN_ROLE_ID, "Manager": TEAM_MANAGER_ROLE_ID,
            "Coach": COACH_ROLE_ID, "Analyst": ANALYST_ROLE_ID, "IGL": IGL_ROLE_ID,
            "Moderator": MODERATOR_ROLE_ID, "Main Team": MAIN_TEAM_ROLE_ID, "Player": PLAYER_ROLE_ID
        }
        
        actual_roles = {}
        for name, rid in role_map.items():
            role = guild.get_role(rid) if rid else discord.utils.get(guild.roles, name=name)
            if not role:
                role = await guild.create_role(name=name, reason="KreeManager Setup")
            actual_roles[name] = role

        structure = {
            "🏠 ONBOARDING": ["welcome", "how-this-server-works", "player-journey", "role-selection"],
            "📢 INFORMATION": ["announcements", "updates", "rules", "faq", "support", "contact-staff"],
            "🤝 COMMUNITY": ["introduce-yourself", "general-chat", "media-share", "clips-highlights", "looking-for-team", "memes"],
            "🎮 TEAM ZONE": ["team-applications", "scrim-results", "team-chat", "roster-management"],
            "📊 PERFORMANCE": ["leaderboards", "attendance-log", "rankings", "performance-reports"],
            "🛡️ STAFF HEADQUARTERS": ["staff-chat", "management-log", "scrim-requests", "reports-admin"],
            "🔊 VOICE CHANNELS": {
                "channels": ["General VC", "Practice Room 1", "Match Room", "Strategy & Analysis", "Team Voice 1", "Team Voice 2", "Scrim Room"],
                "is_vc": True
            }
        }

        for cat_name, chans in structure.items():
            # Get or create category
            norm_cat = self.normalize(cat_name)
            category = None
            for c in guild.categories:
                if self.normalize(c.name) == norm_cat:
                    category = c
                    break
            if not category:
                category = await guild.create_category(cat_name)
                self.created_count += 1
            else:
                try:
                    await category.edit(name=cat_name)
                except: pass
            
            chan_list = chans["channels"] if isinstance(chans, dict) else chans
            is_vc = chans.get("is_vc", False) if isinstance(chans, dict) else False

            for chan_name in chan_list:
                norm_chan = self.normalize(chan_name)
                channel = None
                search_list = guild.voice_channels if is_vc else guild.text_channels
                for c in search_list:
                    if self.normalize(c.name) == norm_chan:
                        channel = c
                        break
                
                if not channel:
                    if is_vc:
                        channel = await guild.create_voice_channel(chan_name, category=category)
                    else:
                        channel = await guild.create_text_channel(chan_name, category=category)
                    self.created_count += 1
                else:
                    try:
                        if channel.category != category:
                            await channel.edit(category=category)
                            self.reused_count += 1
                    except: pass

                
                # CONTENT DEPLOYMENT (Text channels only)
                if not is_vc:
                    try:
                        print(f"[KreeManager] Deploying content to: {chan_name}")
                        if chan_name == "rules": await self.deploy_rules(channel, PLAYER_ROLE_ID)
                        elif chan_name == "how-this-server-works": await self.deploy_how_it_works(channel)
                        elif chan_name == "player-journey": await self.deploy_player_journey(channel)
                        elif chan_name == "role-selection": await self.deploy_role_selection(channel)
                        elif chan_name == "welcome": await self.deploy_welcome_info(channel)
                        elif chan_name == "faq": await self.deploy_faq(channel)
                        elif chan_name == "support": await self.deploy_support(channel)
                        elif chan_name == "announcements": await self.deploy_announcements_intro(channel)
                        elif chan_name == "introduce-yourself": await self.deploy_intro_guide(channel)
                    except Exception as e:
                        print(f"[KreeManager] FAILED content deployment for {chan_name}: {e}")


        # FINAL SUMMARY
        embed = discord.Embed(title="🚀 Ultimate Organization Complete", color=SUCCESS_COLOR)
        embed.description = f"The server infrastructure has been **rebuilt and expanded**.\n\n" \
                            f"♻️ **Merged/Consolidated**: {self.reused_count} structures\n" \
                            f"✨ **Newly Deployed**: {self.created_count} structures\n" \
                            f"📁 **Total Categories**: {len(structure)}"
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def deploy_rules(self, chan, role_id):
        await chan.purge()
        embed = discord.Embed(title="📜 Official Code of Conduct", color=EMBED_COLOR)
        embed.description = "By entering this organization, you agree to the following professional standards:"
        embed.add_field(name="1. Professionalism", value="Maintain a professional attitude in all competitive channels.", inline=False)
        embed.add_field(name="2. Integrity", value="No cheating, strategy leaking, or match-fixing.", inline=False)
        embed.add_field(name="3. Respect", value="Zero tolerance for toxicity towards teammates or opponents.", inline=False)
        await chan.send(embed=embed, view=PersistentRulesView(role_id))

    async def deploy_how_it_works(self, chan):
        await chan.purge()
        embed = discord.Embed(title="📘 How the Organization Operates", color=EMBED_COLOR)
        embed.add_field(name="🏢 Structure", value="We operate in Tiers (T1, T2, T3). Higher tiers get more support.", inline=False)
        embed.add_field(name="📅 Scheduling", value="All matches and practice sessions are posted in `#practice-schedules`.", inline=False)
        embed.add_field(name="📈 Advancement", value="Consistently high performance in scrims leads to tier promotion.", inline=False)
        await chan.send(embed=embed)

    async def deploy_player_journey(self, chan):
        await chan.purge()
        embed = discord.Embed(title="🛤️ Your Professional Roadmap", color=EMBED_COLOR)
        embed.description = "Follow these steps to become a part of our main roster:"
        steps = [
            "1. **Verification**: Accept the code of conduct in `#rules`.",
            "2. **Profile Setup**: Use `/profile_setup` to link your game ID.",
            "3. **Role Selection**: Set your tactical role in `#role-selection`.",
            "4. **Trialing**: Join our community scrims to get noticed by scouts.",
            "5. **Contracting**: Top performers will be invited to the official team."
        ]
        embed.add_field(name="Steps", value="\n".join(steps), inline=False)
        await chan.send(embed=embed)

    async def deploy_role_selection(self, chan):
        await chan.purge()
        embed = discord.Embed(title="🏷️ Tactical Role Assignment", color=EMBED_COLOR)
        embed.description = "Select your primary role to help staff organize teams effectively."
        await chan.send(embed=embed, view=PersistentRoleView())

    async def deploy_welcome_info(self, chan):
        await chan.purge()
        embed = discord.Embed(title="👋 Welcome to the Frontlines", color=EMBED_COLOR)
        embed.description = "You are now part of a premier esports collective.\n\n" \
                            "📍 **Verification**: `#rules` (MANDATORY)\n" \
                            "📍 **Manual**: `#how-this-server-works` (ESSENTIAL)\n" \
                            "📍 **Action**: `#general-chat` (COMMUNITY)"
        await chan.send(embed=embed)

    async def deploy_faq(self, chan):
        await chan.purge()
        embed = discord.Embed(title="❓ Frequently Asked Questions", color=EMBED_COLOR)
        embed.add_field(name="How do I join a team?", value="Complete your profile and participate in trial scrims.", inline=False)
        embed.add_field(name="What is Reliability?", value="A score tracking your attendance and professionalism.", inline=False)
        await chan.send(embed=embed)

    async def deploy_support(self, chan):
        await chan.purge()
        embed = discord.Embed(title="🛠️ Technical Support & Help", color=EMBED_COLOR)
        embed.description = "Need help with the bot or have a dispute? Open a ticket or contact a Manager."
        await chan.send(embed=embed)

    async def deploy_announcements_intro(self, chan):
        await chan.purge()
        embed = discord.Embed(title="📢 Organization Announcements", color=EMBED_COLOR)
        embed.description = "Keep an eye on this channel for official news, match results, and roster changes."
        await chan.send(embed=embed)

    async def deploy_intro_guide(self, chan):
        await chan.purge()
        embed = discord.Embed(title="🤝 Introduce Yourself", color=EMBED_COLOR)
        embed.description = "Tell the community about yourself!\n\n" \
                            "• Your Name/IGN\n" \
                            "• Your Main Game\n" \
                            "• Your Competitive History"
        await chan.send(embed=embed)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_server", description="Intelligently build and clean a professional esports server")
    async def setup_server(self, interaction: discord.Interaction):
        view = SetupView(self.bot, interaction)
        embed = discord.Embed(title="🏢 Elite Organization Deployment", color=EMBED_COLOR)
        embed.description = "This engine will **Clean, Merge, and Deploy** a complete professional infrastructure."
        embed.add_field(name="Current Settings", value="⏳ Waiting for selection...", inline=False)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="audit_server", description="Audit and auto-fix server duplicates, missing content, and role issues")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(auto_fix="Set to True to automatically fix all detected issues")
    async def audit_server(self, interaction: discord.Interaction, auto_fix: bool = False):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        bot_member = guild.me
        bot_top_role = bot_member.top_role

        def normalize(text):
            return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

        # Categories that are managed by trial team engine — exclude from dupe detection
        trial_category_norms = set()
        trial_teams = await self.bot.db.get_all_trial_teams()
        for team in trial_teams:
            cat_id = team[8]
            cat = guild.get_channel(cat_id)
            if cat:
                trial_category_norms.add(cat.id)

        fixes_applied = []

        # ═══════════════════════════════════════════
        # 1. DUPLICATE CATEGORIES (same normalized name)
        # ═══════════════════════════════════════════
        duplicates = []
        cat_groups = {}
        for cat in guild.categories:
            norm = normalize(cat.name)
            if norm not in cat_groups:
                cat_groups[norm] = []
            cat_groups[norm].append(cat)

        for norm, cats in cat_groups.items():
            if len(cats) > 1:
                # Skip trial team categories — they're intentionally separate
                non_trial = [c for c in cats if c.id not in trial_category_norms]
                if len(non_trial) > 1:
                    duplicates.append(f"📁 Category: **{non_trial[0].name}** ({len(non_trial)} copies)")
                    if auto_fix:
                        primary = non_trial[0]
                        for extra in non_trial[1:]:
                            for chan in extra.channels:
                                try:
                                    await chan.edit(category=primary)
                                except: pass
                            try:
                                await extra.delete()
                                fixes_applied.append(f"🗑️ Deleted duplicate category: {extra.name}")
                            except: pass

        # ═══════════════════════════════════════════
        # 2. DUPLICATE CHANNELS (same name + same category)
        # ═══════════════════════════════════════════
        chan_groups = {}
        for chan in guild.text_channels:
            # Only flag duplicates WITHIN the same category
            cat_id = chan.category_id or 0
            key = (normalize(chan.name), cat_id)
            if key not in chan_groups:
                chan_groups[key] = []
            chan_groups[key].append(chan)

        for key, chans in chan_groups.items():
            if len(chans) > 1:
                cat_name = chans[0].category.name if chans[0].category else "No Category"
                duplicates.append(f"💬 #{chans[0].name} in **{cat_name}** ({len(chans)} copies)")
                if auto_fix:
                    # Keep the oldest channel, delete duplicates
                    primary = sorted(chans, key=lambda c: c.created_at)[0]
                    for extra in chans:
                        if extra.id != primary.id:
                            try:
                                await extra.delete()
                                fixes_applied.append(f"🗑️ Deleted duplicate channel: #{extra.name}")
                            except: pass

        # ═══════════════════════════════════════════
        # 3. EMPTY/MISSING SETUP CONTENT
        # ═══════════════════════════════════════════
        # Only check channels in the main setup categories (not trial team categories)
        target_chans = {
            "rules": "Rules & Verification Button",
            "how-this-server-works": "Organization Operations Guide",
            "player-journey": "Player Roadmap Guide",
            "role-selection": "Tactical Role Dropdown",
            "welcome": "Welcome Information Card",
            "faq": "FAQ Guide",
            "support": "Support System Card",
            "announcements": "Announcements Intro",
            "introduce-yourself": "Introduction Templates"
        }

        empty_channels = []
        for chan_slug, description in target_chans.items():
            # Find channel in non-trial categories only
            found_chan = None
            for chan in guild.text_channels:
                if normalize(chan.name) == normalize(chan_slug):
                    if chan.category and chan.category.id in trial_category_norms:
                        continue  # Skip trial team versions
                    found_chan = chan
                    break

            if not found_chan:
                empty_channels.append(f"❌ #{chan_slug} — **Missing entirely** ({description})")
                if auto_fix:
                    # Try to find the right category or create in first available
                    target_cat = None
                    if chan_slug in ["rules", "how-this-server-works", "player-journey", "role-selection", "welcome"]:
                        for cat in guild.categories:
                            if normalize(cat.name) in [normalize("🏠 ONBOARDING"), normalize("ONBOARDING")]:
                                target_cat = cat
                                break
                    elif chan_slug in ["faq", "support", "announcements"]:
                        for cat in guild.categories:
                            if normalize(cat.name) in [normalize("📢 INFORMATION"), normalize("INFORMATION")]:
                                target_cat = cat
                                break
                    elif chan_slug == "introduce-yourself":
                        for cat in guild.categories:
                            if normalize(cat.name) in [normalize("🤝 COMMUNITY"), normalize("COMMUNITY")]:
                                target_cat = cat
                                break

                    if target_cat:
                        try:
                            new_chan = await guild.create_text_channel(chan_slug, category=target_cat)
                            fixes_applied.append(f"✨ Created missing channel: #{chan_slug}")
                            found_chan = new_chan  # So content deploy below can use it
                        except Exception as e:
                            fixes_applied.append(f"❌ Failed to create #{chan_slug}: {e}")
            else:
                # Check if channel has bot content
                try:
                    messages = []
                    async for msg in found_chan.history(limit=5):
                        messages.append(msg)
                    bot_msgs = [m for m in messages if m.author.id == self.bot.user.id]
                    if not bot_msgs:
                        empty_channels.append(f"⚠️ #{found_chan.name} — **No bot content** ({description})")
                except Exception as e:
                    empty_channels.append(f"❌ #{found_chan.name} — Error reading: {e}")

            # Auto-fix: Deploy content to empty/new channels
            if auto_fix and found_chan:
                try:
                    bot_msgs = []
                    async for msg in found_chan.history(limit=5):
                        if msg.author.id == self.bot.user.id:
                            bot_msgs.append(msg)
                    if not bot_msgs:
                        # Deploy the correct content
                        view = SetupView(self.bot, interaction)
                        from config import PLAYER_ROLE_ID
                        if chan_slug == "rules":
                            await view.deploy_rules(found_chan, PLAYER_ROLE_ID)
                            fixes_applied.append(f"📜 Deployed Rules & Verify button to #{found_chan.name}")
                        elif chan_slug == "how-this-server-works":
                            await view.deploy_how_it_works(found_chan)
                            fixes_applied.append(f"📘 Deployed Operations Guide to #{found_chan.name}")
                        elif chan_slug == "player-journey":
                            await view.deploy_player_journey(found_chan)
                            fixes_applied.append(f"🛤️ Deployed Player Journey to #{found_chan.name}")
                        elif chan_slug == "role-selection":
                            await view.deploy_role_selection(found_chan)
                            fixes_applied.append(f"🏷️ Deployed Role Selection to #{found_chan.name}")
                        elif chan_slug == "welcome":
                            await view.deploy_welcome_info(found_chan)
                            fixes_applied.append(f"👋 Deployed Welcome Info to #{found_chan.name}")
                        elif chan_slug == "faq":
                            await view.deploy_faq(found_chan)
                            fixes_applied.append(f"❓ Deployed FAQ to #{found_chan.name}")
                        elif chan_slug == "support":
                            await view.deploy_support(found_chan)
                            fixes_applied.append(f"🛠️ Deployed Support Card to #{found_chan.name}")
                        elif chan_slug == "announcements":
                            await view.deploy_announcements_intro(found_chan)
                            fixes_applied.append(f"📢 Deployed Announcements Intro to #{found_chan.name}")
                        elif chan_slug == "introduce-yourself":
                            await view.deploy_intro_guide(found_chan)
                            fixes_applied.append(f"🤝 Deployed Intro Guide to #{found_chan.name}")
                except Exception as e:
                    fixes_applied.append(f"❌ Content deploy error for #{chan_slug}: {e}")

        # ═══════════════════════════════════════════
        # 4. ROLE HIERARCHY + MISSING ROLES
        # ═══════════════════════════════════════════
        from config import (
            OWNER_ROLE_ID, ADMIN_ROLE_ID, TEAM_MANAGER_ROLE_ID, COACH_ROLE_ID,
            ANALYST_ROLE_ID, IGL_ROLE_ID, MODERATOR_ROLE_ID, MAIN_TEAM_ROLE_ID,
            PLAYER_ROLE_ID
        )

        role_map = {
            "Owner": OWNER_ROLE_ID, "Admin": ADMIN_ROLE_ID, "Manager": TEAM_MANAGER_ROLE_ID,
            "Coach": COACH_ROLE_ID, "Analyst": ANALYST_ROLE_ID, "IGL": IGL_ROLE_ID,
            "Moderator": MODERATOR_ROLE_ID, "Main Team": MAIN_TEAM_ROLE_ID, "Player": PLAYER_ROLE_ID
        }

        hierarchy_warnings = []
        missing_roles = []
        for name, rid in role_map.items():
            role = guild.get_role(rid) if rid else discord.utils.get(guild.roles, name=name)
            if not role:
                missing_roles.append(name)
                if auto_fix:
                    try:
                        new_role = await guild.create_role(name=name, reason="KreeManager Audit Auto-Fix")
                        fixes_applied.append(f"🏷️ Created missing role: **{name}**")
                    except Exception as e:
                        fixes_applied.append(f"❌ Failed to create role {name}: {e}")
            else:
                if role.position >= bot_top_role.position and not role.is_default():
                    hierarchy_warnings.append(f"⚠️ **{role.name}** is above the bot's role")

        # ═══════════════════════════════════════════
        # 5. BOT PERMISSIONS CHECK
        # ═══════════════════════════════════════════
        permission_warnings = []
        perms = bot_member.guild_permissions
        if not perms.manage_roles:
            permission_warnings.append("❌ Missing **Manage Roles** permission")
        if not perms.manage_channels:
            permission_warnings.append("❌ Missing **Manage Channels** permission")
        if not perms.manage_messages:
            permission_warnings.append("❌ Missing **Manage Messages** permission")

        # ═══════════════════════════════════════════
        # BUILD REPORT
        # ═══════════════════════════════════════════
        has_issues = duplicates or empty_channels or hierarchy_warnings or missing_roles or permission_warnings

        if auto_fix and fixes_applied:
            embed = discord.Embed(title="🔧 KreeManager Auto-Fix Report", color=SUCCESS_COLOR)
            embed.description = f"**{len(fixes_applied)} fixes applied** to the server infrastructure."
            fix_text = "\n".join(fixes_applied[:15])
            embed.add_field(name="Actions Taken", value=fix_text, inline=False)

            # Remaining issues that couldn't be auto-fixed
            remaining = []
            if hierarchy_warnings:
                remaining.extend(hierarchy_warnings)
            if permission_warnings:
                remaining.extend(permission_warnings)
            if remaining:
                embed.add_field(name="⚠️ Requires Manual Fix", value="\n".join(remaining[:10]), inline=False)
                embed.set_footer(text="Role hierarchy and bot permissions must be fixed manually in Server Settings.")
            else:
                embed.set_footer(text="All fixable issues resolved!")

        elif auto_fix and not fixes_applied and not has_issues:
            embed = discord.Embed(title="🔍 KreeManager Infrastructure Audit", color=SUCCESS_COLOR)
            embed.description = "🟢 **All systems operational!** Nothing to fix."

        else:
            embed = discord.Embed(title="🔍 KreeManager Infrastructure Audit", color=EMBED_COLOR)

            if not has_issues:
                embed.description = "🟢 **All systems operational!** Server is clean and compliant."
            else:
                embed.description = "⚠️ **Issues detected.** Run `/audit_server auto_fix:True` to auto-repair.\n"

                if duplicates:
                    embed.add_field(name="🚨 Duplicate Structures", value="\n".join(duplicates[:10]), inline=False)
                if empty_channels:
                    embed.add_field(name="📝 Missing Content", value="\n".join(empty_channels[:10]), inline=False)
                if hierarchy_warnings:
                    embed.add_field(name="🛡️ Role Hierarchy Conflicts", value="\n".join(hierarchy_warnings[:10]), inline=False)
                if missing_roles:
                    embed.add_field(name="🏷️ Missing Roles", value=", ".join(missing_roles), inline=False)
                if permission_warnings:
                    embed.add_field(name="⚙️ Missing Permissions", value="\n".join(permission_warnings), inline=False)

            embed.set_footer(text="Tip: /audit_server auto_fix:True to auto-repair")

        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
