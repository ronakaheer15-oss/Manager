import discord
from discord import app_commands
from discord.ext import commands
from config import EMBED_COLOR

class Profiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="View a player's esports profile")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        player = await self.bot.db.get_player(member.id)
        
        if not player:
            if member == interaction.user:
                await interaction.response.send_message("You don't have a profile yet! Use `/editprofile` to create one.", ephemeral=True)
            else:
                await interaction.response.send_message(f"{member.display_name} doesn't have a profile yet.", ephemeral=True)
            return

        # player schema: 0:discord_id, 1:ign, 2:uid, 3:role, 4:device, 5:kd, 6:rank, 7:exp, 8:strengths, 9:weaknesses, 10:avail, 11:tier, 12:status, 13:on_vacation, 14:vacation_reason, 15:vacation_until, 16:last_seen, 17:team_id, 18:join_date
        ign = player[1]
        uid = player[2]
        role = player[3]
        tier = player[11]
        join_date = player[18]

        embed = discord.Embed(title=f"🎮 {ign}'s Profile", color=EMBED_COLOR)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="IGN", value=ign or "N/A", inline=True)
        embed.add_field(name="UID", value=uid or "N/A", inline=True)
        embed.add_field(name="Tier", value=tier or "Tier 4", inline=True)
        embed.add_field(name="Role", value=role or "N/A", inline=True)
        embed.add_field(name="Joined", value=join_date or "Unknown", inline=True)
        embed.add_field(name="Status", value=player[12] or "Active", inline=True)
        
        embed.add_field(name="KD", value=str(player[5]), inline=True)
        embed.add_field(name="Rank", value=player[6] or "N/A", inline=True)
        embed.add_field(name="Device", value=player[4] or "N/A", inline=True)
        
        embed.add_field(name="Availability", value=player[10] or "N/A", inline=True)
        embed.add_field(name="Experience", value=player[7] or "N/A", inline=False)
        embed.add_field(name="Strengths", value=player[8] or "N/A", inline=True)
        embed.add_field(name="Weaknesses", value=player[9] or "N/A", inline=True)
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="request_vacation", description="Request a vacation from the team")
    @app_commands.describe(reason="Why do you need a vacation?", duration="How many days do you need?")
    async def request_vacation(self, interaction: discord.Interaction, reason: str, duration: int):
        await self.bot.db.update_player(interaction.user.id, vacation_reason=reason)
        
        # Notify staff channel
        channel_id = await self.bot.db.get_setting("announcement_channel")
        channel = self.bot.get_channel(int(channel_id)) if channel_id else interaction.channel
        
        embed = discord.Embed(title="🏖️ New Vacation Request", color=discord.Color.blue())
        embed.add_field(name="Player", value=interaction.user.mention)
        embed.add_field(name="Duration", value=f"{duration} Days")
        embed.add_field(name="Reason", value=reason)
        embed.set_footer(text="Staff: Use /approve_vacation to grant this request.")
        
        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Your vacation request has been submitted to the Staff for approval.", ephemeral=True)


    @app_commands.command(name="editprofile", description="Edit your esports profile")

    async def editprofile(self, interaction: discord.Interaction, ign: str = None, uid: str = None, role: str = None, device: str = None, rank: str = None, experience: str = None, strengths: str = None, weaknesses: str = None, availability: str = None):
        player = await self.bot.db.get_player(interaction.user.id)
        
        if not player:
            if not ign:
                await interaction.response.send_message("Please provide an IGN to create your profile!", ephemeral=True)
                return
            await self.bot.db.create_player(interaction.user.id, ign)
        
        updates = {}
        if ign: updates['ign'] = ign
        if uid: updates['uid'] = uid
        if role: updates['role'] = role
        if device: updates['device'] = device
        if rank: updates['rank'] = rank
        if experience: updates['experience'] = experience
        if strengths: updates['strengths'] = strengths
        if weaknesses: updates['weaknesses'] = weaknesses
        if availability: updates['availability'] = availability
        
        if updates:
            await self.bot.db.update_player(interaction.user.id, **updates)
            await interaction.response.send_message("✅ Profile updated successfully!", ephemeral=True)
        else:
            await interaction.response.send_message("No changes provided.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Profiles(bot))
