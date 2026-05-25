import discord
from discord.ext import commands
from discord import app_commands
import os
import aiosqlite
from utils.ai_parser import analyze_screenshot_for_stats, parse_natural_language_command
from config import EMBED_COLOR

class AITracking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_reports = {}

    def find_member_by_name(self, guild, name_query):
        name_query = name_query.lower().strip()
        # Search members in guild
        for member in guild.members:
            if name_query in member.display_name.lower() or name_query in member.name.lower():
                return member
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # 1. Handle DM interactive mapping (KreeRank feature)
        if isinstance(message.channel, discord.DMChannel) and message.author.id in self.pending_reports:
            target_member = None
            if message.mentions:
                target_member = message.mentions[0]
            else:
                # We need a guild context to search for members. 
                # We'll use the first mutual guild.
                if message.author.mutual_guilds:
                    target_member = self.find_member_by_name(message.author.mutual_guilds[0], message.content)

            if target_member:
                report_data = self.pending_reports.pop(message.author.id)
                stats = report_data['stats']
                ign = report_data['unknown_name']
                
                # Update IGN mapping in KreeManager DB
                await self.bot.db.update_player(target_member.id, ign=ign)
                
                # Log Stats
                await self.bot.db.add_stats(
                    target_member.id, 
                    stats.get('kills', 0), stats.get('assists', 0), stats.get('survival_time', 0),
                    stats.get('clutches', 0), stats.get('teamplay', 5), stats.get('communication', 5),
                    stats.get('discipline', 5), stats.get('mistakes', 0)
                )
                
                await message.channel.send(f"✅ Linked IGN **{ign}** to **{target_member.display_name}** and logged stats!")
                return

        # 2. Monitor Report Channel
        report_channel_id = await self.bot.db.get_setting("report_channel_id")
        if report_channel_id and str(message.channel.id) == str(report_channel_id):
            if message.attachments:
                attachment = message.attachments[0]
                if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    async with message.channel.typing():
                        temp_path = f"KreeManager/data/temp_{attachment.id}.png"
                        os.makedirs("KreeManager/data", exist_ok=True)
                        await attachment.save(temp_path)
                        
                        try:
                            stats = analyze_screenshot_for_stats(temp_path, message.content or "")
                            os.remove(temp_path)
                            
                            # Try to find player by IGN or Mention
                            target_member = None
                            if message.mentions:
                                target_member = message.mentions[0]
                            else:
                                # Search DB for IGN
                                players = await self.bot.db.get_all_players()
                                # KreeManager schema index 1 is IGN
                                for p in players:
                                    if p[1] and p[1].lower() in message.content.lower():
                                        target_member = message.guild.get_member(p[0])
                                        break
                            
                            if not target_member:
                                self.pending_reports[message.author.id] = {
                                    "stats": stats,
                                    "unknown_name": "Detected Player",
                                    "guild_id": message.guild.id
                                }
                                await message.channel.send(f"❓ **AI found stats but no player linked!**\nStats: {stats}\n\n**{message.author.mention}, please check your DMs to link this player!**")
                                try:
                                    await message.author.send("Who is the player in this screenshot? Please type their Discord name or mention them.")
                                except: pass
                                return

                            # Log to DB
                            await self.bot.db.add_stats(
                                target_member.id, 
                                stats.get('kills', 0), stats.get('assists', 0), stats.get('survival_time', 0),
                                stats.get('clutches', 0), stats.get('teamplay', 5), stats.get('communication', 5),
                                stats.get('discipline', 5), stats.get('mistakes', 0)
                            )
                            
                            embed = discord.Embed(title="🤖 AI Match Report Logged", color=EMBED_COLOR)
                            embed.add_field(name="Player", value=target_member.mention)
                            embed.add_field(name="Kills", value=stats.get('kills', 0))
                            embed.add_field(name="Assists", value=stats.get('assists', 0))
                            await message.channel.send(embed=embed)
                        except Exception as e:
                            await message.channel.send(f"❌ AI Error: {str(e)}")

    @app_commands.command(name="set_report_channel", description="Set the channel where AI will listen for match screenshots")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_report_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.db.set_setting("report_channel_id", str(channel.id))
        await interaction.response.send_message(f"✅ AI will now listen for screenshots in {channel.mention}!")

async def setup(bot):
    await bot.add_cog(AITracking(bot))
