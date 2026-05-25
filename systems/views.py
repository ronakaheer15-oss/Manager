import discord
from config import EMBED_COLOR

class PersistentRulesView(discord.ui.View):
    def __init__(self, role_id):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(label="Accept & Verify", style=discord.ButtonStyle.success, custom_id="verify_button_persistent")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        print(f"[KreeManager] Verification attempt by {interaction.user} (ID: {interaction.user.id})")
        
        # Try finding role by ID
        role = interaction.guild.get_role(self.role_id) if self.role_id else None
        
        # Try finding role by name if ID failed
        if not role:
            role = discord.utils.get(interaction.guild.roles, name="Player")
        if not role:
            role = discord.utils.get(interaction.guild.roles, name="Main Team")
            
        if role:
            try:
                await interaction.user.add_roles(role)
                
                # Dynamic Trial Team Assignment
                trial_engine = interaction.client.get_cog('TrialTeamEngine')
                if trial_engine:
                    try:
                        team_name = await trial_engine.assign_player_to_trial_team(interaction.user)
                        await interaction.followup.send(f"✅ Verification Successful! Access Granted.\n🏆 You have been rostered onto **{team_name}**. Check your new team category to begin training!", ephemeral=True)
                    except Exception as e:
                        print(f"[KreeManager] Onboarding error: {e}")
                        await interaction.followup.send("✅ Verification Successful! (There was a delay routing you to a Trial Team. Contact Management.)", ephemeral=True)
                else:
                    await interaction.followup.send("✅ Verification Successful! Access Granted.", ephemeral=True)
                
                print(f"[KreeManager] Successfully verified {interaction.user}")
            except Exception as e:
                await interaction.followup.send(f"❌ Permission Error: Bot cannot assign roles. {e}", ephemeral=True)
        else:
            await interaction.followup.send("❌ Error: Verification role not found. Please contact an Admin to run `/setup_server`.", ephemeral=True)



class PersistentRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(placeholder="Choose your Tactical Role", options=[
        discord.SelectOption(label="IGL", value="igl", emoji="👑"),
        discord.SelectOption(label="Assaulter", value="assaulter", emoji="⚔️"),
        discord.SelectOption(label="Sniper", value="sniper", emoji="🎯"),
        discord.SelectOption(label="Support", value="support", emoji="🛡️")
    ], custom_id="role_select_persistent")
    async def select_role(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.send_message(f"✅ Your tactical role has been set to **{select.values[0].upper()}**.", ephemeral=True)

async def setup(bot):
    pass

