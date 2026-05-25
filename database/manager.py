import aiosqlite
import os

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Teams Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    manager_id INTEGER,
                    tier TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Pending Approvals (for Crucial Roles)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS pending_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_type TEXT,
                    target_id INTEGER,
                    requested_role_id INTEGER,
                    requester_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Player Profiles (Updated for Discipline & Verification)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    discord_id INTEGER PRIMARY KEY,
                    ign TEXT,
                    uid TEXT,
                    role TEXT,
                    device TEXT,
                    kd REAL DEFAULT 0.0,
                    rank TEXT,
                    experience TEXT,
                    strengths TEXT,
                    weaknesses TEXT,
                    availability TEXT,
                    tier TEXT DEFAULT 'Tier 4',
                    status TEXT DEFAULT 'Active',
                    on_vacation BOOLEAN DEFAULT 0,
                    vacation_reason TEXT,
                    vacation_until DATE,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    team_id INTEGER,
                    join_date DATE DEFAULT CURRENT_DATE,
                    discipline_score INTEGER DEFAULT 100,
                    reliability_score INTEGER DEFAULT 100,
                    verification_status TEXT DEFAULT 'Unverified'
                )
            """)

            # Discipline History
            await db.execute("""
                CREATE TABLE IF NOT EXISTS discipline_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    action_type TEXT,
                    reason TEXT,
                    staff_id INTEGER,
                    duration_minutes INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Appeals System
            await db.execute("""
                CREATE TABLE IF NOT EXISTS appeals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    discipline_id INTEGER,
                    reason TEXT,
                    status TEXT DEFAULT 'Pending',
                    staff_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)


            # Financial Ledger
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT,
                    amount REAL,
                    player_id INTEGER,
                    status TEXT DEFAULT 'Unpaid',
                    due_date DATE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Scrim Challenges
            await db.execute("""
                CREATE TABLE IF NOT EXISTS scrim_challenges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    opponent_name TEXT,
                    opponent_contact TEXT,
                    date_time DATETIME,
                    status TEXT DEFAULT 'Pending'
                )
            """)


            
            # Performance Stats
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER,
                    kills INTEGER DEFAULT 0,
                    assists INTEGER DEFAULT 0,
                    survival_time INTEGER DEFAULT 0,
                    clutches INTEGER DEFAULT 0,
                    teamplay INTEGER DEFAULT 0,
                    communication INTEGER DEFAULT 0,
                    discipline INTEGER DEFAULT 0,
                    mistakes INTEGER DEFAULT 0,
                    mvp_count INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Map Intelligence
            await db.execute("""
                CREATE TABLE IF NOT EXISTS map_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    map_name TEXT,
                    team_id INTEGER,
                    result TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)


            # Coach Playbook
            await db.execute("""
                CREATE TABLE IF NOT EXISTS playbook (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    strategy_link TEXT,
                    category TEXT,
                    added_by INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)


            # Attendance
            await db.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER,
                    date DATE,
                    status TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Warnings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER,
                    reason TEXT,
                    admin_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Economy
            await db.execute("""
                CREATE TABLE IF NOT EXISTS economy (
                    discord_id INTEGER PRIMARY KEY,
                    balance INTEGER DEFAULT 0
                )
            """)

            # Scrims
            await db.execute("""
                CREATE TABLE IF NOT EXISTS scrims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATETIME,
                    opponent TEXT,
                    result TEXT,
                    notes TEXT,
                    reminders_sent BOOLEAN DEFAULT 0
                )
            """)

            # Tournaments
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tournaments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    date DATETIME,
                    registration_status TEXT,
                    prize TEXT,
                    room_id TEXT,
                    room_password TEXT
                )
            """)

            # Server Settings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Ensure report_channel exists
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('report_channel_id', '0')")

            # Trial Teams
            await db.execute("""
                CREATE TABLE IF NOT EXISTS trial_teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    role_id INTEGER,
                    captain_role_id INTEGER,
                    manager_role_id INTEGER,
                    coach_role_id INTEGER,
                    analyst_role_id INTEGER,
                    player_role_id INTEGER,
                    category_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Trial Goals
            await db.execute("""
                CREATE TABLE IF NOT EXISTS trial_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_id INTEGER,
                    goal_text TEXT,
                    target_value INTEGER,
                    current_value INTEGER DEFAULT 0,
                    deadline DATETIME,
                    status TEXT DEFAULT 'Pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(team_id) REFERENCES trial_teams(id) ON DELETE CASCADE
                )
            """)

            # Trial Logs
            await db.execute("""
                CREATE TABLE IF NOT EXISTS trial_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT,
                    details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)



            # 🚀 DATABASE MIGRATIONS (Ensure columns exist for existing databases)

            async with db.execute("PRAGMA table_info(players)") as cursor:
                columns = [row[1] for row in await cursor.fetchall()]
                
                # Check and Add Missing Columns
                if "on_vacation" not in columns:
                    await db.execute("ALTER TABLE players ADD COLUMN on_vacation BOOLEAN DEFAULT 0")
                if "vacation_reason" not in columns:
                    await db.execute("ALTER TABLE players ADD COLUMN vacation_reason TEXT")
                if "vacation_until" not in columns:
                    await db.execute("ALTER TABLE players ADD COLUMN vacation_until DATE")
                if "last_seen" not in columns:
                    await db.execute("ALTER TABLE players ADD COLUMN last_seen DATETIME DEFAULT CURRENT_TIMESTAMP")
                if "team_id" not in columns:
                    await db.execute("ALTER TABLE players ADD COLUMN team_id INTEGER")
                if "join_date" not in columns:
                    await db.execute("ALTER TABLE players ADD COLUMN join_date DATE DEFAULT CURRENT_DATE")
                if "tier" not in columns:
                    await db.execute("ALTER TABLE players ADD COLUMN tier TEXT DEFAULT 'Tier 4'")
                if "status" not in columns:
                    await db.execute("ALTER TABLE players ADD COLUMN status TEXT DEFAULT 'Active'")
                if "discipline_score" not in columns:
                    await db.execute("ALTER TABLE players ADD COLUMN discipline_score INTEGER DEFAULT 100")
                if "reliability_score" not in columns:
                    await db.execute("ALTER TABLE players ADD COLUMN reliability_score INTEGER DEFAULT 100")
                if "verification_status" not in columns:
                    await db.execute("ALTER TABLE players ADD COLUMN verification_status TEXT DEFAULT 'Unverified'")

            # 🚀 PERFORMANCE OPTIMIZATION: Indexing for Scalability
            await db.execute("CREATE INDEX IF NOT EXISTS idx_players_last_seen ON players(last_seen)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_stats_discord_id ON stats(discord_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_map_stats_team_id ON map_stats(team_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_warnings_discord_id ON warnings(discord_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_discipline_player_id ON discipline_history(player_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_appeals_status ON appeals(status)")


            await db.commit()



    async def set_setting(self, key, value):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            await db.commit()

    async def get_setting(self, key):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None

    async def get_player(self, discord_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,)) as cursor:
                return await cursor.fetchone()

    async def update_player(self, discord_id, **kwargs):
        async with aiosqlite.connect(self.db_path) as db:
            cols = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            vals = list(kwargs.values())
            vals.append(discord_id)
            await db.execute(f"UPDATE players SET {cols} WHERE discord_id = ?", vals)
            await db.commit()

    async def create_player(self, discord_id, ign):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO players (discord_id, ign) VALUES (?, ?)", (discord_id, ign))
            await db.commit()
            
    async def add_stats(self, discord_id, kills, assists, survival, clutches, teamplay, communication, discipline, mistakes):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO stats (discord_id, kills, assists, survival_time, clutches, teamplay, communication, discipline, mistakes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (discord_id, kills, assists, survival, clutches, teamplay, communication, discipline, mistakes))
            await db.commit()
            
    async def get_balance(self, discord_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT balance FROM economy WHERE discord_id = ?", (discord_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def update_balance(self, discord_id, amount):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO economy (discord_id, balance) VALUES (?, ?)
                ON CONFLICT(discord_id) DO UPDATE SET balance = balance + ?
            """, (discord_id, amount, amount))
            await db.commit()

    async def get_all_players(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM players") as cursor:
                return await cursor.fetchall()

    async def add_attendance(self, discord_id, date, status):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO attendance (discord_id, date, status) VALUES (?, ?, ?)", (discord_id, date, status))
            await db.commit()
            
    async def get_attendance_report(self, date):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT p.ign, a.status FROM attendance a JOIN players p ON a.discord_id = p.discord_id WHERE a.date = ?", (date,)) as cursor:
                return await cursor.fetchall()

    async def get_leaderboard(self, category="kills"):
        async with aiosqlite.connect(self.db_path) as db:
            if category == "kills":
                query = "SELECT p.ign, SUM(s.kills) as total FROM stats s JOIN players p ON s.discord_id = p.discord_id GROUP BY s.discord_id ORDER BY total DESC LIMIT 10"
            elif category == "mvp":
                query = "SELECT p.ign, SUM(s.mvp_count) as total FROM stats s JOIN players p ON s.discord_id = p.discord_id GROUP BY s.discord_id ORDER BY total DESC LIMIT 10"
            else: # rating based
                query = "SELECT p.ign, SUM(s.kills*2 + s.assists + s.clutches*5 + s.teamplay + s.communication + s.discipline - s.mistakes*3) as total FROM stats s JOIN players p ON s.discord_id = p.discord_id GROUP BY s.discord_id ORDER BY total DESC LIMIT 10"
            
            async with db.execute(query) as cursor:
                return await cursor.fetchall()

    async def create_scrim(self, date, opponent, notes):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO scrims (date, opponent, notes) VALUES (?, ?, ?)", (date, opponent, notes))
            await db.commit()

    async def update_scrim_result(self, scrim_id, result):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE scrims SET result = ? WHERE id = ?", (result, scrim_id))
            await db.commit()

    async def get_scrim_history(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM scrims ORDER BY date DESC LIMIT 10") as cursor:
                return await cursor.fetchall()

    async def create_tournament(self, name, date, prize):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO tournaments (name, date, prize, registration_status) VALUES (?, ?, ?, 'Registered')", (name, date, prize))
            await db.commit()

    async def update_tournament_room(self, tourney_id, room_id, password):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE tournaments SET room_id = ?, room_password = ? WHERE id = ?", (room_id, password, tourney_id))
            await db.commit()

    async def get_tournaments(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM tournaments ORDER BY date DESC LIMIT 10") as cursor:
                return await cursor.fetchall()

    async def add_warning(self, discord_id, reason, admin_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO warnings (discord_id, reason, admin_id) VALUES (?, ?, ?)", (discord_id, reason, admin_id))
            await db.commit()

    async def get_warnings(self, discord_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM warnings WHERE discord_id = ?", (discord_id,)) as cursor:
                return await cursor.fetchall()

    async def clear_warnings(self, discord_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM warnings WHERE discord_id = ?", (discord_id,))
            await db.commit()

    async def get_player_stats(self, discord_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM stats WHERE discord_id = ? ORDER BY timestamp DESC LIMIT 5", (discord_id,)) as cursor:
                return await cursor.fetchall()

    async def set_vacation(self, discord_id, status: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE players SET on_vacation = ? WHERE discord_id = ?", (status, discord_id))
            await db.commit()

    async def update_last_seen(self, discord_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE players SET last_seen = CURRENT_TIMESTAMP WHERE discord_id = ?", (discord_id,))
            await db.commit()

    async def get_inactive_players(self, days=3):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT discord_id, ign FROM players WHERE last_seen < datetime('now', '-' || ? || ' days') AND on_vacation = 0", (days,)) as cursor:
                return await cursor.fetchall()

    async def create_trial_team(self, name, role_id, captain_role_id, manager_role_id, coach_role_id, analyst_role_id, player_role_id, category_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                INSERT INTO trial_teams (name, role_id, captain_role_id, manager_role_id, coach_role_id, analyst_role_id, player_role_id, category_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, role_id, captain_role_id, manager_role_id, coach_role_id, analyst_role_id, player_role_id, category_id)) as cursor:
                await db.commit()
                return cursor.lastrowid

    async def get_trial_team(self, team_id=None, name=None):
        async with aiosqlite.connect(self.db_path) as db:
            if team_id is not None:
                async with db.execute("SELECT * FROM trial_teams WHERE id = ?", (team_id,)) as cursor:
                    return await cursor.fetchone()
            elif name is not None:
                async with db.execute("SELECT * FROM trial_teams WHERE name = ?", (name,)) as cursor:
                    return await cursor.fetchone()
        return None

    async def get_all_trial_teams(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM trial_teams") as cursor:
                return await cursor.fetchall()

    async def delete_trial_team(self, team_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM trial_teams WHERE id = ?", (team_id,))
            await db.commit()

    async def add_trial_goal(self, team_id, goal_text, target_value, deadline_days):
        async with aiosqlite.connect(self.db_path) as db:
            deadline = datetime.datetime.now() + datetime.timedelta(days=deadline_days)
            async with db.execute("""
                INSERT INTO trial_goals (team_id, goal_text, target_value, current_value, deadline)
                VALUES (?, ?, ?, 0, ?)
            """, (team_id, goal_text, target_value, deadline.strftime('%Y-%m-%d %H:%M:%S'))) as cursor:
                await db.commit()
                return cursor.lastrowid

    async def get_team_goals(self, team_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM trial_goals WHERE team_id = ?", (team_id,)) as cursor:
                return await cursor.fetchall()

    async def update_trial_goal_progress(self, goal_id, progress):
        async with aiosqlite.connect(self.db_path) as db:
            # Check target first
            async with db.execute("SELECT target_value FROM trial_goals WHERE id = ?", (goal_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    target = row[0]
                    status = 'Completed' if progress >= target else 'Pending'
                    await db.execute("UPDATE trial_goals SET current_value = ?, status = ? WHERE id = ?", (progress, status, goal_id))
                    await db.commit()

    async def evaluate_goals(self):
        expired_goals = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT g.id, g.team_id, g.goal_text, t.name FROM trial_goals g JOIN trial_teams t ON g.team_id = t.id WHERE g.status = 'Pending' AND g.deadline < CURRENT_TIMESTAMP") as cursor:
                expired_goals = await cursor.fetchall()
            for g_id, _, _, _ in expired_goals:
                await db.execute("UPDATE trial_goals SET status = 'Failed' WHERE id = ?", (g_id,))
            await db.commit()
        return expired_goals

    async def log_trial_action(self, action_type, details):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO trial_logs (action_type, details) VALUES (?, ?)", (action_type, details))
            await db.commit()

    async def get_trial_logs(self, limit=50):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM trial_logs ORDER BY timestamp DESC LIMIT ?", (limit,)) as cursor:
                return await cursor.fetchall()

    async def get_trial_team_players(self, team_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM players WHERE team_id = ?", (team_id,)) as cursor:
                return await cursor.fetchall()

