import discord
from discord.ext import commands
from config import EMBED_COLOR

class WelcomeEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        # Find welcome channel (Smart Detection)
        welcome_chan = None
        for chan in guild.text_channels:
            if "welcome" in chan.name.lower():
                welcome_chan = chan
                break
        
        if not welcome_chan:
            return

        embed = discord.Embed(title=f"🔥 Welcome to {guild.name}, {member.display_name}!", color=EMBED_COLOR)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.description = (
            f"You have entered an elite, automated competitive esports platform. Here is your onboarding journey:\n\n"
            f"🏁 **Step 1: Code of Conduct & Verification**\n"
            f"Read `#rules` and click **Accept & Verify** to unlock the server.\n\n"
            f"🗺️ **Step 2: Server Structure & Goals**\n"
            f"Familiarize yourself with organization workflows in `#how-this-server-works`.\n\n"
            f"🏆 **Step 3: Tryout & Placement Queue**\n"
            f"Upon verification, KreeManager will **automatically slot you** into a dynamic Trial Team, create your team channels, and assign your tactical cohort. You'll work together on team goals to get promoted to our permanent rosters.\n\n"
            f"Let's make history. See you on the battlefield! 🏅"
        )
        embed.set_footer(text=f"Recruit #{guild.member_count}")
        
        try:
            await welcome_chan.send(content=f"Welcome {member.mention}!", embed=embed)
        except Exception as e:
            print(f"Failed to send welcome message: {e}")


async def setup(bot):
    await bot.add_cog(WelcomeEvents(bot))
