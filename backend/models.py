"""
Data models for the Outreach Engine
"""
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class CommunicationStyle(str, Enum):
    """Enum for communication styles"""
    FORMAL = "formal"
    SEMI_FORMAL = "semi_formal"
    CASUAL = "casual"
    VERY_CASUAL = "very_casual"
    MIXED = "mixed"


class SocialMediaPlatform(str, Enum):
    """Supported social media platforms"""
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    GITHUB = "github"
    PERSONAL_WEBSITE = "personal_website"


class OutreachChannel(str, Enum):
    """Outreach channels for message generation"""
    EMAIL = "email"
    LINKEDIN_DM = "linkedin_dm"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    INSTAGRAM_DM = "instagram_dm"


class UserProfile(BaseModel):
    """User profile extracted from social media"""
    id: Optional[str] = None
    name: str
    email: Optional[str] = None
    role: str
    company: str
    industry: str
    location: Optional[str] = None
    bio: str
    about: Optional[str] = None
    skills: List[str] = []
    interests: List[str] = []
    recent_activity: List[str] = []
    education: Optional[str] = None
    seniority_level: str  # junior, mid, senior, lead, founder, etc.
    communication_style: CommunicationStyle = CommunicationStyle.MIXED
    language: str = "english"
    uses_emojis: bool = False
    uses_slang: bool = False
    uses_abbreviations: bool = False
    formal_percentage: float = 0.5  # 0-1, how formal they are
    source_platform: SocialMediaPlatform
    profile_url: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    raw_data: Dict[str, Any] = {}

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "role": "Product Manager",
                "company": "TechCorp",
                "industry": "Technology",
                "bio": "Building AI products | Coffee enthusiast",
                "seniority_level": "senior",
                "communication_style": "semi_formal",
                "source_platform": "linkedin",
                "profile_url": "https://linkedin.com/in/johndoe"
            }
        }


class GeneratedMessage(BaseModel):
    """Generated outreach message"""
    channel: OutreachChannel
    subject: Optional[str] = None  # For email
    content: str
    cta: str  # Call to action
    tone: CommunicationStyle
    estimated_reply_rate: Optional[float] = None  # AI-estimated likelihood
    variations: List[str] = []  # Alternative versions


class OutreachRequest(BaseModel):
    """Request to generate outreach messages"""
    profile_url: str
    platform: SocialMediaPlatform
    channels: List[OutreachChannel] = [
        OutreachChannel.EMAIL,
        OutreachChannel.LINKEDIN_DM,
        OutreachChannel.WHATSAPP
    ]
    additional_context: Optional[str] = None
    include_variations: bool = False


class OutreachResponse(BaseModel):
    """Response with generated messages"""
    profile: UserProfile
    messages: List[GeneratedMessage]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    profile_saved: bool = False


class StoredProfile(BaseModel):
    """Stored profile for knowledge reuse"""
    id: str
    profile: UserProfile
    messages_generated: int = 0
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}


class AnalyticsEvent(BaseModel):
    """Analytics event tracking"""
    event_type: str
    user_id: Optional[str] = None
    profile_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = {}


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    is_model_loaded: bool
    device: str
    uptime_seconds: Optional[float] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    details: Optional[str] = None
    code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
