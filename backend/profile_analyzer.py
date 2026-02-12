"""
Profile Analyzer for extracting and analyzing social media profiles
"""
import logging
import re
from typing import Dict, List, Tuple
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from backend.models import (
    UserProfile,
    CommunicationStyle,
    SocialMediaPlatform,
)
from backend.config import settings

logger = logging.getLogger(__name__)


class ProfileAnalyzer:
    """Analyzes social media profiles and extracts structured information"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def analyze_linkedin_profile(self, profile_data: Dict) -> UserProfile:
        """Analyze LinkedIn profile data (mock implementation for demo)"""
        return self._create_profile_from_data(
            profile_data, SocialMediaPlatform.LINKEDIN
        )

    def analyze_twitter_profile(self, profile_data: Dict) -> UserProfile:
        """Analyze Twitter/X profile data (mock implementation for demo)"""
        return self._create_profile_from_data(
            profile_data, SocialMediaPlatform.TWITTER
        )

    def analyze_github_profile(self, profile_data: Dict) -> UserProfile:
        """Analyze GitHub profile data (mock implementation for demo)"""
        return self._create_profile_from_data(
            profile_data, SocialMediaPlatform.GITHUB
        )

    def _create_profile_from_data(
        self, data: Dict, platform: SocialMediaPlatform
    ) -> UserProfile:
        """Create UserProfile from raw data"""

        # Extract basic info
        name = data.get("name", "Unknown User")
        email = data.get("email", "")
        role = data.get("role", "Professional")
        company = data.get("company", "")
        industry = data.get("industry", "Technology")
        bio = data.get("bio", "")
        about = data.get("about", "")
        skills = data.get("skills", [])
        interests = data.get("interests", [])
        location = data.get("location", "")
        education = data.get("education", "")
        recent_activity = data.get("recent_activity", [])

        # Analyze communication style
        style, metrics = self._analyze_communication_style(
            bio, about, recent_activity
        )

        # Determine seniority level
        seniority = self._determine_seniority(role, data.get("years_experience", 0))

        profile = UserProfile(
            name=name,
            email=email,
            role=role,
            company=company,
            industry=industry,
            location=location,
            bio=bio,
            about=about,
            skills=skills,
            interests=interests,
            recent_activity=recent_activity,
            education=education,
            seniority_level=seniority,
            communication_style=style,
            uses_emojis=metrics["uses_emojis"],
            uses_slang=metrics["uses_slang"],
            uses_abbreviations=metrics["uses_abbreviations"],
            formal_percentage=metrics["formal_percentage"],
            source_platform=platform,
            profile_url=data.get("profile_url", ""),
            raw_data=data,
            language=data.get("language", "english"),
        )

        return profile

    def _analyze_communication_style(
        self, bio: str, about: str, recent_activity: List[str]
    ) -> Tuple[CommunicationStyle, Dict]:
        """Analyze communication style from text"""
        text = f"{bio} {about} {' '.join(recent_activity)}".lower()

        # Initialize metrics
        metrics = {
            "uses_emojis": False,
            "uses_slang": False,
            "uses_abbreviations": False,
            "formal_percentage": 0.5,
        }

        # Detect emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "]+",
            flags=re.UNICODE,
        )
        metrics["uses_emojis"] = bool(emoji_pattern.search(text))

        # Detect slang and casual language
        slang_words = [
            "lol",
            "omg",
            "tbh",
            "ngl",
            "idk",
            "gonna",
            "wanna",
            "kinda",
            "dunno",
        ]
        metrics["uses_slang"] = any(word in text for word in slang_words)

        # Detect abbreviations
        abbreviations = ["asap", "etc", "fyi", "btw", "imho", "imo"]
        metrics["uses_abbreviations"] = any(abbr in text for abbr in abbreviations)

        # Calculate formality percentage
        formal_words = [
            "professional",
            "expertise",
            "leverage",
            "synergy",
            "strategic",
            "initiative",
            "implement",
        ]
        informal_words = slang_words + ["cool", "awesome", "love", "hate", "fun"]

        formal_count = sum(1 for word in formal_words if word in text)
        informal_count = sum(1 for word in informal_words if word in text)

        if formal_count + informal_count > 0:
            metrics["formal_percentage"] = formal_count / (
                formal_count + informal_count
            )
        else:
            metrics["formal_percentage"] = 0.5  # Default neutral

        # Determine overall style
        if metrics["formal_percentage"] > 0.7:
            style = CommunicationStyle.FORMAL
        elif metrics["formal_percentage"] > 0.5:
            style = CommunicationStyle.SEMI_FORMAL
        elif metrics["formal_percentage"] < 0.3:
            style = CommunicationStyle.VERY_CASUAL
        elif metrics["formal_percentage"] < 0.5:
            style = CommunicationStyle.CASUAL
        else:
            style = CommunicationStyle.MIXED

        return style, metrics

    def _determine_seniority(self, role: str, years_experience: int = 0) -> str:
        """Determine seniority level from role"""
        role_lower = role.lower()

        if any(
            keyword in role_lower
            for keyword in [
                "founder",
                "ceo",
                "cto",
                "cfo",
                "president",
                "chief",
            ]
        ):
            return "founder"
        elif any(
            keyword in role_lower
            for keyword in ["director", "vp", "vice president", "head of"]
        ):
            return "senior"
        elif any(
            keyword in role_lower for keyword in ["lead", "principal", "staff"]
        ):
            return "lead"
        elif any(
            keyword in role_lower for keyword in ["senior", "sr.", "sr "]
        ):
            return "senior"
        elif any(
            keyword in role_lower
            for keyword in ["mid", "intermediate", "specialist"]
        ):
            return "mid"
        elif any(
            keyword in role_lower for keyword in ["junior", "jr.", "jr ", "intern"]
        ):
            return "junior"
        elif any(
            keyword in role_lower for keyword in ["student", "fresh", "graduate"]
        ):
            return "junior"
        else:
            # Estimate from years
            if years_experience >= 15:
                return "senior"
            elif years_experience >= 8:
                return "mid"
            elif years_experience >= 3:
                return "junior"
            else:
                return "junior"

    def extract_insights(self, profile: UserProfile) -> Dict:
        """Extract actionable insights from profile"""
        insights = {
            "pain_points": self._identify_pain_points(profile),
            "interests": profile.interests,
            "achievements": self._extract_achievements(profile),
            "communication_style": profile.communication_style.value,
            "best_channels": self._recommend_channels(profile),
        }
        return insights

    def _identify_pain_points(self, profile: UserProfile) -> List[str]:
        """Identify potential pain points based on profile"""
        pain_points = []

        role_lower = profile.role.lower()
        company_size = len(profile.company) if profile.company else 0

        if any(
            keyword in role_lower
            for keyword in ["product", "manager", "pm", "product manager"]
        ):
            pain_points.extend([
                "User retention and engagement",
                "Feature prioritization",
                "Cross-functional coordination",
            ])

        if any(keyword in role_lower for keyword in ["founder", "ceo", "startup"]):
            pain_points.extend([
                "Team scaling",
                "Product-market fit",
                "Fundraising",
            ])

        if any(
            keyword in role_lower
            for keyword in ["engineer", "developer", "dev", "cto"]
        ):
            pain_points.extend([
                "Technical debt",
                "Team productivity",
                "System reliability",
            ])

        if any(
            keyword in role_lower
            for keyword in ["marketing", "growth", "sales"]
        ):
            pain_points.extend([
                "Lead generation",
                "Conversion optimization",
                "Customer acquisition cost",
            ])

        return pain_points

    def _extract_achievements(self, profile: UserProfile) -> List[str]:
        """Extract achievements from profile"""
        achievements = []

        if profile.education:
            achievements.append(f"Educated at {profile.education}")

        if profile.company:
            achievements.append(f"Works at {profile.company}")

        if profile.skills:
            achievements.append(f"Skills: {', '.join(profile.skills[:3])}")

        return achievements

    def _recommend_channels(self, profile: UserProfile) -> List[str]:
        """Recommend outreach channels based on profile"""
        channels = ["email"]

        if profile.email or profile.source_platform == SocialMediaPlatform.LINKEDIN:
            channels.append("linkedin_dm")

        if profile.uses_slang or profile.communication_style in [
            CommunicationStyle.CASUAL,
            CommunicationStyle.VERY_CASUAL,
        ]:
            channels.extend(["whatsapp", "instagram_dm"])
        else:
            channels.append("sms")

        return channels
