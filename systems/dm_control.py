import discord
from discord.ext import commands
from config import ADMIN_ROLE_ID, COACH_ROLE_ID

class DMControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="dm_announce")
    @commands.dm_only()
    async def dm_announce(self, ctx, channel_id: int, *, message: str):
        # Secure check
        is_staff = False
        for guild in self.bot.guilds:
            member = guild.get_member(ctx.author.id)
            if member and (member.guild_permissions.administrator or any(role.id in [ADMIN_ROLE_ID, COACH_ROLE_ID] for role in member.roles)):
                is_staff = True
                break
        
        if not is_staff:
            await ctx.send("❌ Access Denied. Admin/Coach permissions required.")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            await ctx.send("❌ Channel not found.")
            return

        embed = discord.Embed(title="📢 Team Announcement", description=message, color=0xFF4500)
        embed.set_footer(text="Official Announcement via KreeManager")
        try:
            await channel.send(embed=embed)
            await ctx.send(f"✅ Announcement sent to <#{channel_id}>.")
        except Exception as e:
            await ctx.send(f"❌ Failed to send message: {e}")

async def setup(bot):
    await bot.add_cog(DMControl(bot))
