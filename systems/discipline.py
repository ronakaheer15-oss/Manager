import discord
from discord import app_commands
from discord.ext import commands
import datetime
from config import EMBED_COLOR, ERROR_COLOR, SUCCESS_COLOR

class Discipline(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="warn", description="Issue a professional warning to a player")
    @app_commands.describe(member="The player to warn", reason="Reason for the warning")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        # 1. LOG TO DATABASE
        await self.bot.db.add_warning(member.id, reason, interaction.user.id)
        
        # 2. GET WARNING COUNT & ESCALATE
        warnings = await self.bot.db.get_warnings(member.id)
        count = len(warnings)
        
        # 3. UPDATE DISCIPLINE SCORE
        player = await self.bot.db.get_player(member.id)
        new_score = max(0, (player[19] if player else 100) - 10)
        await self.bot.db.update_player(member.id, discipline_score=new_score)

        # 4. ESCALATION LOGIC
        escalation_msg = ""
        if count == 2:
            escalation_msg = "\n⚠️ **Escalation**: Next offense will result in a timeout."
        elif count == 3:
            try:
                await member.timeout(datetime.timedelta(hours=1), reason="3rd Warning Escalation")
                escalation_msg = "\n🔇 **Escalation**: 1 Hour Timeout applied (3rd Warning)."
            except:
                escalation_msg = "\n❌ Failed to apply timeout. Check permissions."
        elif count >= 4:
            escalation_msg = "\n🚫 **Escalation**: Immediate suspension required. Notify Management."

        # 5. EMBED RESPONSE
        embed = discord.Embed(title="🛡️ Disciplinary Action: Warning", color=ERROR_COLOR)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Player", value=member.mention, inline=True)
        embed.add_field(name="Staff", value=interaction.user.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Warning Count", value=f"**{count}**", inline=True)
        embed.add_field(name="Discipline Score", value=f"**{new_score}/100**", inline=True)
        if escalation_msg:
            embed.description = escalation_msg
            
        await interaction.response.send_message(embed=embed)
        
        # DM THE PLAYER
        try:
            dm_embed = discord.Embed(title="⚠️ Official Warning Issued", color=ERROR_COLOR)
            dm_embed.description = f"You have been warned in **{interaction.guild.name}**.\n\n**Reason:** {reason}\n**Total Warnings:** {count}"
            dm_embed.set_footer(text="Please maintain professionalism to avoid further escalation.")
            await member.send(embed=dm_embed)
        except:
            pass

    @app_commands.command(name="history", description="View disciplinary history of a player")
    @app_commands.describe(member="The player to check")
    async def history(self, interaction: discord.Interaction, member: discord.Member):
        warnings = await self.bot.db.get_warnings(member.id)
        player = await self.bot.db.get_player(member.id)
        
        embed = discord.Embed(title=f"📊 Discipline Profile: {member.display_name}", color=EMBED_COLOR)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        score = player[19] if player else "N/A"
        reliability = player[20] if player else "N/A"
        
        embed.add_field(name="Discipline Score", value=f"**{score}/100**", inline=True)
        embed.add_field(name="Reliability", value=f"**{reliability}/100**", inline=True)
        
        if not warnings:
            embed.description = "✅ No disciplinary records found for this player."
        else:
            history_text = ""
            for w in warnings[-5:]: # Last 5 warnings
                timestamp = w[4] if isinstance(w[4], str) else "Recent"
                history_text += f"• `{timestamp}`: {w[2]} (by <@{w[3]}>)\n"
            embed.add_field(name="Recent Violations", value=history_text, inline=False)
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="discipline_score", description="Check a player's discipline and reliability scores")
    @app_commands.describe(member="The player to check")
    async def discipline_score(self, interaction: discord.Interaction, member: discord.Member):
        player = await self.bot.db.get_player(member.id)
        if not player:
            await interaction.response.send_message("❌ Player not found in database.", ephemeral=True)
            return

        # Calculate Real-time Reliability
        attendance = await self.bot.db.get_attendance_report(str(datetime.date.today()))
        # This is a placeholder for a more complex rolling average calculation
        # In a real system, we would query the last 30 days of attendance
        
        discipline_score = player[19]
        reliability_score = player[20]
        
        embed = discord.Embed(title=f"🏆 Professional Standing: {member.display_name}", color=EMBED_COLOR)
        embed.add_field(name="🛡️ Discipline Score", value=f"**{discipline_score}/100**", inline=True)
        embed.add_field(name="📈 Reliability Score", value=f"**{reliability_score}/100**", inline=True)
        
        status = "🟢 Excellent" if reliability_score > 90 else "🟡 Average" if reliability_score > 70 else "🔴 Poor"
        embed.add_field(name="Status", value=status, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="update_reliability", description="Recalculate reliability for all players (Admin Only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def update_reliability(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        players = await self.bot.db.get_all_players()
        
        for p in players:
            discord_id = p[0]
            # Reliability = (Attendance % * 0.7) + (Discipline Score * 0.3)
            # Fetch attendance count vs total days (simplified here)
            new_reliability = min(100, int((p[19] * 0.5) + 50)) # Placeholder formula
            await self.bot.db.update_player(discord_id, reliability_score=new_reliability)
            
        await interaction.followup.send("✅ Reliability scores updated for all players.")

async def setup(bot):

    await bot.add_cog(Discipline(bot))
