import discord
from discord.ext import commands
import datetime
from config import EMBED_COLOR, ERROR_COLOR

class ModerationEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_messages = {} # For spam detection

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # 1. TOXICITY & BANNED WORDS FILTER
        banned_words = ["toxic", "noob", "garbage", "trash", "retard", "ez", "hacker"] # Example list
        content_lower = message.content.lower()
        
        for word in banned_words:
            if word in content_lower:
                await self.handle_violation(message, f"Toxic Language Detection: '{word}'")
                return

        # 2. SPAM DETECTION (Rate limiting)
        user_id = message.author.id
        now = datetime.datetime.now()
        
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        
        self.user_messages[user_id].append(now)
        # Keep only last 5 seconds of messages
        self.user_messages[user_id] = [t for t in self.user_messages[user_id] if (now - t).total_seconds() < 5]
        
        if len(self.user_messages[user_id]) > 5:
            await self.handle_violation(message, "Message Spamming")
            return

        # 3. MASS PING DETECTION
        if len(message.mentions) > 5:
            await self.handle_violation(message, "Mass Ping Attempt")
            return

    async def handle_violation(self, message, reason):
        try:
            await message.delete()
        except:
            pass

        # Log to Database
        await self.bot.db.add_warning(message.author.id, f"[Auto-Mod] {reason}", self.bot.user.id)
        
        # Update Discipline Score
        player = await self.bot.db.get_player(message.author.id)
        if player:
            new_score = max(0, player[19] - 5)
            await self.bot.db.update_player(message.author.id, discipline_score=new_score)

        # Notify User
        try:
            embed = discord.Embed(title="🛡️ Auto-Mod Warning", color=ERROR_COLOR)
            embed.description = f"Your message was removed in **{message.guild.name}**.\n\n**Reason:** {reason}\n**Discipline Score:** {new_score if player else 'N/A'}/100"
            await message.author.send(embed=embed)
        except:
            pass

        # Log to Management Channel
        log_channel_id = await self.bot.db.get_setting("management_log_channel")
        if log_channel_id:
            log_channel = message.guild.get_channel(int(log_channel_id))
            if log_channel:
                log_embed = discord.Embed(title="🚨 Auto-Mod Action", color=ERROR_COLOR)
                log_embed.add_field(name="User", value=message.author.mention, inline=True)
                log_embed.add_field(name="Reason", value=reason, inline=True)
                log_embed.add_field(name="Original Content", value=f"||{message.content}||", inline=False)
                await log_channel.send(embed=log_embed)

async def setup(bot):
    await bot.add_cog(ModerationEvents(bot))
