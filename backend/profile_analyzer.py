"""
Profile Analyzer for extracting and analyzing social media profiles
"""

import logging
import re
from typing import Dict, List, Tuple
import requests

from backend.models import (
    UserProfile,
    CommunicationStyle,
    SocialMediaPlatform,
)

logger = logging.getLogger(__name__)


class ProfileAnalyzer:
    """Analyzes social media profiles and extracts structured information"""

    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "]+",
        flags=re.UNICODE,
    )

    SLANG_WORDS = [
        "lol", "omg", "tbh", "ngl", "idk",
        "gonna", "wanna", "kinda", "dunno"
    ]

    ABBREVIATIONS = ["asap", "etc", "fyi", "btw", "imho", "imo"]

    FORMAL_WORDS = [
        "professional", "expertise", "leverage",
        "synergy", "strategic", "initiative", "implement"
    ]

    INFORMAL_WORDS = SLANG_WORDS + ["cool", "awesome", "love", "hate", "fun"]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36"
                )
            }
        )

    # ==============================
    # Platform Analyzers
    # ==============================

    def analyze_linkedin_profile(self, profile_data: Dict) -> UserProfile:
        return self._create_profile_from_data(
            profile_data, SocialMediaPlatform.LINKEDIN
        )

    def analyze_twitter_profile(self, profile_data: Dict) -> UserProfile:
        return self._create_profile_from_data(
            profile_data, SocialMediaPlatform.TWITTER
        )

    def analyze_github_profile(self, profile_data: Dict) -> UserProfile:
        return self._create_profile_from_data(
            profile_data, SocialMediaPlatform.GITHUB
        )

    # ==============================
    # Core Profile Builder
    # ==============================

    def _create_profile_from_data(
        self, data: Dict, platform: SocialMediaPlatform
    ) -> UserProfile:

        name = data.get("name", "Unknown User")
        role = data.get("role", "Professional")
        bio = data.get("bio", "")
        about = data.get("about", "")
        recent_activity = data.get("recent_activity", [])

        style, metrics = self._analyze_communication_style(
            bio, about, recent_activity
        )

        seniority = self._determine_seniority(
            role, data.get("years_experience", 0)
        )

        return UserProfile(
            name=name,
            email=data.get("email", ""),
            role=role,
            company=data.get("company", ""),
            industry=data.get("industry", "Technology"),
            location=data.get("location", ""),
            bio=bio,
            about=about,
            skills=data.get("skills", []),
            interests=data.get("interests", []),
            recent_activity=recent_activity,
            education=data.get("education", ""),
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

    # ==============================
    # Communication Analysis
    # ==============================

    def _analyze_communication_style(
        self, bio: str, about: str, recent_activity: List[str]
    ) -> Tuple[CommunicationStyle, Dict]:

        text = f"{bio} {about} {' '.join(recent_activity)}".lower()

        metrics = {
            "uses_emojis": bool(self.EMOJI_PATTERN.search(text)),
            "uses_slang": any(word in text for word in self.SLANG_WORDS),
            "uses_abbreviations": any(abbr in text for abbr in self.ABBREVIATIONS),
            "formal_percentage": 0.5,
        }

        formal_count = sum(word in text for word in self.FORMAL_WORDS)
        informal_count = sum(word in text for word in self.INFORMAL_WORDS)

        total = formal_count + informal_count
        if total > 0:
            metrics["formal_percentage"] = formal_count / total

        fp = metrics["formal_percentage"]

        if fp >= 0.75:
            style = CommunicationStyle.FORMAL
        elif fp >= 0.55:
            style = CommunicationStyle.SEMI_FORMAL
        elif fp <= 0.25:
            style = CommunicationStyle.VERY_CASUAL
        elif fp <= 0.45:
            style = CommunicationStyle.CASUAL
        else:
            style = CommunicationStyle.MIXED

        return style, metrics

    # ==============================
    # Seniority Logic
    # ==============================

    def _determine_seniority(self, role: str, years_experience: int = 0) -> str:
        role_lower = role.lower()

        if any(k in role_lower for k in
               ["founder", "ceo", "cto", "cfo", "president", "chief"]):
            return "founder"

        if any(k in role_lower for k in
               ["director", "vp", "vice president", "head of"]):
            return "senior"

        if any(k in role_lower for k in
               ["lead", "principal", "staff"]):
            return "lead"

        if "senior" in role_lower:
            return "senior"

        if any(k in role_lower for k in
               ["mid", "intermediate", "specialist"]):
            return "mid"

        if any(k in role_lower for k in
               ["junior", "intern", "student", "graduate", "jr"]):
            return "junior"

        # fallback on experience
        if years_experience >= 12:
            return "senior"
        if years_experience >= 6:
            return "mid"

        return "junior"

    # ==============================
    # Insights Extraction
    # ==============================

    def extract_insights(self, profile: UserProfile) -> Dict:
        return {
            "pain_points": self._identify_pain_points(profile),
            "interests": profile.interests,
            "achievements": self._extract_achievements(profile),
            "communication_style": profile.communication_style.value,
            "best_channels": self._recommend_channels(profile),
        }

    def _identify_pain_points(self, profile: UserProfile) -> List[str]:
        role_lower = profile.role.lower()
        pain_points = []

        if any(k in role_lower for k in ["product manager", "pm", "product"]):
            pain_points += [
                "User retention and engagement",
                "Feature prioritization",
                "Cross-functional coordination",
            ]

        if any(k in role_lower for k in ["founder", "ceo", "startup"]):
            pain_points += [
                "Team scaling",
                "Product-market fit",
                "Fundraising",
            ]

        if any(k in role_lower for k in ["engineer", "developer", "cto"]):
            pain_points += [
                "Technical debt",
                "Team productivity",
                "System reliability",
            ]

        if any(k in role_lower for k in ["marketing", "growth", "sales"]):
            pain_points += [
                "Lead generation",
                "Conversion optimization",
                "Customer acquisition cost",
            ]

        return pain_points

    def _extract_achievements(self, profile: UserProfile) -> List[str]:
        achievements = []

        if profile.education:
            achievements.append(f"Educated at {profile.education}")

        if profile.company:
            achievements.append(f"Works at {profile.company}")

        if profile.skills:
            achievements.append(
                f"Skills: {', '.join(profile.skills[:3])}"
            )

        return achievements

    def _recommend_channels(self, profile: UserProfile) -> List[str]:
        channels = ["email"]

        if profile.email or profile.source_platform == SocialMediaPlatform.LINKEDIN:
            channels.append("linkedin_dm")

        if profile.uses_slang or profile.communication_style in [
            CommunicationStyle.CASUAL,
            CommunicationStyle.VERY_CASUAL,
        ]:
            channels += ["whatsapp", "instagram_dm"]
        else:
            channels.append("sms")

        return channels
