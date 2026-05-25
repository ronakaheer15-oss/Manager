import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_PATH = "KreeManager/database/kree_manager.db"

# Visuals
EMBED_COLOR = 0xFF4500  # Orange-Red (Kree Flame)
SUCCESS_COLOR = 0x2ECC71
ERROR_COLOR = 0xE74C3C

# Roles
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", 0))
COACH_ROLE_ID = int(os.getenv("COACH_ROLE_ID", 0))
PLAYER_ROLE_ID = int(os.getenv("PLAYER_ROLE_ID", 0))
TEAM_MANAGER_ROLE_ID = int(os.getenv("TEAM_MANAGER_ROLE_ID", 0))
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", 0))

# Tactical Roles
IGL_ROLE_ID = int(os.getenv("IGL_ROLE_ID", 0))
ASSAULTER_ROLE_ID = int(os.getenv("ASSAULTER_ROLE_ID", 0))
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID", 0))
ENTRY_FRAGGER_ROLE_ID = int(os.getenv("ENTRY_FRAGGER_ROLE_ID", 0))
SNIPER_ROLE_ID = int(os.getenv("SNIPER_ROLE_ID", 0))

# Organizational Roles
OWNER_ROLE_ID = int(os.getenv("OWNER_ROLE_ID", 0))
ANALYST_ROLE_ID = int(os.getenv("ANALYST_ROLE_ID", 0))
MODERATOR_ROLE_ID = int(os.getenv("MODERATOR_ROLE_ID", 0))
MAIN_TEAM_ROLE_ID = int(os.getenv("MAIN_TEAM_ROLE_ID", 0))
PRACTICE_TEAM_ROLE_ID = int(os.getenv("PRACTICE_TEAM_ROLE_ID", 0))
ACADEMY_TEAM_ROLE_ID = int(os.getenv("ACADEMY_TEAM_ROLE_ID", 0))
TRIAL_PLAYER_ROLE_ID = int(os.getenv("TRIAL_PLAYER_ROLE_ID", 0))
CONTENT_CREATOR_ROLE_ID = int(os.getenv("CONTENT_CREATOR_ROLE_ID", 0))

# Version
VERSION = "1.1.0"
BOT_NAME = "🔥 KreeManager"
