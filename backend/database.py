"""
Database handler for storing and retrieving profiles locally
Uses SQLite for lightweight, file-based storage
"""
import json
import logging
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import sqlite3

from backend.models import UserProfile, StoredProfile
from backend.config import settings

logger = logging.getLogger(__name__)


class LocalDatabase:
    """Manages local storage of profiles using SQLite"""

    def __init__(self):
        self.db_path = settings.DB_PATH
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create profiles table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS profiles (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        role TEXT NOT NULL,
                        company TEXT,
                        email TEXT,
                        platform TEXT,
                        profile_url TEXT,
                        data JSON,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                    """
                )

                # Create interactions table for analytics
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        profile_id TEXT,
                        action TEXT,
                        data JSON,
                        timestamp TIMESTAMP,
                        FOREIGN KEY(profile_id) REFERENCES profiles(id)
                    )
                    """
                )

                # Create messages table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        profile_id TEXT,
                        channel TEXT,
                        subject TEXT,
                        content TEXT,
                        cta TEXT,
                        tone TEXT,
                        created_at TIMESTAMP,
                        FOREIGN KEY(profile_id) REFERENCES profiles(id)
                    )
                    """
                )

                conn.commit()
                logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def save_profile(self, profile: UserProfile) -> bool:
        """Save a profile to database"""
        try:
            profile_id = self._generate_id(
                profile.name, profile.company, profile.email
            )

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Serialize profile data
                data = json.dumps(profile.model_dump())

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO profiles
                    (id, name, role, company, email, platform, profile_url, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        profile_id,
                        profile.name,
                        profile.role,
                        profile.company,
                        profile.email,
                        profile.source_platform.value,
                        profile.profile_url,
                        data,
                        profile.last_updated,
                        datetime.utcnow(),
                    ),
                )

                conn.commit()
                logger.info(f"Profile saved: {profile.name}")
                return True

        except Exception as e:
            logger.error(f"Error saving profile: {e}")
            return False

    def get_profile(self, profile_id: str) -> Optional[UserProfile]:
        """Retrieve a profile from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT data FROM profiles WHERE id = ?", (profile_id,)
                )
                row = cursor.fetchone()

                if row:
                    data = json.loads(row["data"])
                    return UserProfile(**data)
                return None

        except Exception as e:
            logger.error(f"Error retrieving profile: {e}")
            return None

    def get_profile_by_name_and_company(
        self, name: str, company: str
    ) -> Optional[UserProfile]:
        """Find profile by name and company"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT data FROM profiles WHERE name LIKE ? AND company LIKE ?",
                    (f"%{name}%", f"%{company}%"),
                )
                row = cursor.fetchone()

                if row:
                    data = json.loads(row["data"])
                    return UserProfile(**data)
                return None

        except Exception as e:
            logger.error(f"Error retrieving profile: {e}")
            return None

    def search_profiles(
        self, query: str, limit: int = 10
    ) -> List[UserProfile]:
        """Search profiles by name, company, or role"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                search_term = f"%{query}%"
                cursor.execute(
                    """
                    SELECT data FROM profiles
                    WHERE name LIKE ? OR company LIKE ? OR role LIKE ?
                    LIMIT ?
                    """,
                    (search_term, search_term, search_term, limit),
                )

                profiles = []
                for row in cursor.fetchall():
                    data = json.loads(row["data"])
                    profiles.append(UserProfile(**data))

                return profiles

        except Exception as e:
            logger.error(f"Error searching profiles: {e}")
            return []

    def get_profiles_by_industry(
        self, industry: str, limit: int = 10
    ) -> List[UserProfile]:
        """Get all profiles from a specific industry"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT data FROM profiles
                    WHERE industry LIKE ?
                    LIMIT ?
                    """,
                    (f"%{industry}%", limit),
                )

                profiles = []
                for row in cursor.fetchall():
                    data = json.loads(row["data"])
                    profiles.append(UserProfile(**data))

                return profiles

        except Exception as e:
            logger.error(f"Error getting profiles by industry: {e}")
            return []

    def save_interaction(
        self, profile_id: str, action: str, data: dict
    ) -> bool:
        """Save user interaction for analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO interactions (profile_id, action, data, timestamp)
                    VALUES (?, ?, ?, ?)
                    """,
                    (profile_id, action, json.dumps(data), datetime.utcnow()),
                )

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error saving interaction: {e}")
            return False

    def get_similar_profiles(
        self, profile: UserProfile, limit: int = 5
    ) -> List[UserProfile]:
        """Find similar profiles (same industry/role) for knowledge reuse"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT data FROM profiles
                    WHERE (industry LIKE ? OR role LIKE ?)
                    AND id != ?
                    LIMIT ?
                    """,
                    (
                        f"%{profile.industry}%",
                        f"%{profile.role}%",
                        profile.id,
                        limit,
                    ),
                )

                similar = []
                for row in cursor.fetchall():
                    data = json.loads(row["data"])
                    similar.append(UserProfile(**data))

                return similar

        except Exception as e:
            logger.error(f"Error finding similar profiles: {e}")
            return []

    def _generate_id(self, name: str, company: str, email: str) -> str:
        """Generate unique profile ID"""
        if email:
            return email.lower()
        return f"{name.lower().replace(' ', '_')}_{company.lower().replace(' ', '_')}"

    def export_profiles(self, format: str = "json") -> str:
        """Export all profiles to file"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM profiles")
                profiles = [dict(row) for row in cursor.fetchall()]

                if format == "json":
                    export_path = (
                        settings.DATA_DIR / "profiles_export.json"
                    )
                    with open(export_path, "w") as f:
                        json.dump(profiles, f, indent=2, default=str)

                return str(export_path)

        except Exception as e:
            logger.error(f"Error exporting profiles: {e}")
            return ""

    def get_database_stats(self) -> dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM profiles")
                profile_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM messages")
                message_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM interactions")
                interaction_count = cursor.fetchone()[0]

                return {
                    "total_profiles": profile_count,
                    "total_messages": message_count,
                    "total_interactions": interaction_count,
                    "database_size": self.db_path.stat().st_size,
                }

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}


# Global database instance
_db_instance: Optional[LocalDatabase] = None


def get_database() -> LocalDatabase:
    """Get or create database singleton"""
    global _db_instance
    if _db_instance is None:
        _db_instance = LocalDatabase()
    return _db_instance
