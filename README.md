# 🔥 KreeManager - Professional Esports Team Management Bot

KreeManager is an all-in-one Discord bot designed for BGMI and other esports organizations. It handles everything from roster management and performance tracking to scrim logistics and economy.

## 🚀 Key Features

*   **Team Management:** Manage rosters, tiers (T1/T2/T3), and roles (IGL, Filter, Support).
*   **Player Profiles:** Comprehensive profiles with KD, Rank, Device, and Experience.
*   **Performance Tracking:** Log kills, assists, survival, and clutches to generate AI-driven ratings.
*   **Leaderboards:** Categorized rankings for Kills, MVP, and overall Performance.
*   **Scrim & Tournaments:** Schedule scrims, log results, and manage tournament room IDs/Passwords.
*   **Attendance:** Track practice participation with daily and weekly reports.
*   **Discipline:** Warning system to track toxicity and inactivity.
*   **Economy:** Reward players with Team Coins for good performance.
*   **DM Controls:** Admins can manage announcements and stats remotely via bot DMs.

## 🛠️ Setup Instructions

1.  **Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration:**
    - Copy `.env.example` to `.env`.
    - Fill in your `DISCORD_TOKEN`.
    - Set the `ADMIN_ROLE_ID`, `COACH_ROLE_ID`, and `PLAYER_ROLE_ID`.

3.  **Bot Permissions:**
    - Ensure the bot has the following intents enabled in the Discord Developer Portal:
        - Presence Intent
        - Server Members Intent
        - Message Content Intent

4.  **Run the Bot:**
    ```bash
    python bot.py
    ```

## 🎮 Commands Reference

### Player Commands
*   `/profile [@member]` - View an esports profile.
*   `/editprofile` - Create or edit your profile.
*   `/leaderboard [category]` - View the team leaderboards.
*   `/wallet` - Check your Team Coin balance.
*   `/shop` - View rewards available in the team shop.

### Management Commands (Admin/Coach)
*   `/promote <@member> <tier>` - Promote a player.
*   `/logstats <@member> <kills> ...` - Log performance data.
*   `/attendance <@member> <status>` - Mark practice attendance.
*   `/scrimcreate <opponent> <date>` - Schedule a scrim.
*   `/match <tourney_id> <room_id> <pass>` - Set room details.
*   `/warn <@member> <reason>` - Issue a warning.
*   `!dm_announce <channel_id> <message>` - Send announcement from DMs (Admin only).

---

Built with ❤️ by Antigravity for Professional Esports Organizations.
