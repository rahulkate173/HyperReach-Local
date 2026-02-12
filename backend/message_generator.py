"""
Message Generator for creating personalized outreach messages
Uses BitNet LLM for tone-matched, context-aware message generation
"""
import logging
from typing import List, Optional
from backend.models import (
    UserProfile,
    GeneratedMessage,
    OutreachChannel,
    CommunicationStyle,
)
from backend.llm_handler import get_llm_handler
from backend.profile_analyzer import ProfileAnalyzer

logger = logging.getLogger(__name__)


class MessageGenerator:
    """Generates personalized outreach messages using BitNet LLM"""

    def __init__(self):
        self.llm = get_llm_handler()
        self.analyzer = ProfileAnalyzer()
        self.max_retries = 3

    def generate_outreach_messages(
        self,
        profile: UserProfile,
        channels: List[OutreachChannel],
        additional_context: Optional[str] = None,
    ) -> List[GeneratedMessage]:
        """Generate personalized messages for specified channels"""
        messages = []

        insights = self.analyzer.extract_insights(profile)

        for channel in channels:
            try:
                message = self._generate_message_for_channel(
                    profile, channel, insights, additional_context
                )
                if message:
                    messages.append(message)
            except Exception as e:
                logger.error(
                    f"Error generating message for {channel.value}: {e}"
                )
                continue

        return messages

    def _generate_message_for_channel(
        self,
        profile: UserProfile,
        channel: OutreachChannel,
        insights: dict,
        additional_context: Optional[str] = None,
    ) -> Optional[GeneratedMessage]:
        """Generate a message for a specific channel"""

        prompt = self._build_prompt(
            profile, channel, insights, additional_context
        )

        try:
            content = self.llm.generate_text(
                prompt,
                max_tokens=200,
                temperature=0.7,
            )

            if not content.strip():
                logger.warning(
                    f"Empty content generated for {channel.value}"
                )
                return None

            # Extract CTA from content or generate one
            cta = self._extract_or_generate_cta(content, profile, channel)

            # Generate subject for email
            subject = None
            if channel == OutreachChannel.EMAIL:
                subject = self._generate_email_subject(profile, insights)

            message = GeneratedMessage(
                channel=channel,
                subject=subject,
                content=content.strip(),
                cta=cta,
                tone=profile.communication_style,
                estimated_reply_rate=self._estimate_reply_rate(
                    profile, content
                ),
            )

            return message

        except Exception as e:
            logger.error(f"Error in message generation: {e}")
            return None

    def _build_prompt(
        self,
        profile: UserProfile,
        channel: OutreachChannel,
        insights: dict,
        additional_context: Optional[str] = None,
    ) -> str:
        """Build a detailed prompt for LLM"""

        style_description = self._describe_communication_style(
            profile.communication_style, profile
        )

        channel_instructions = self._get_channel_instructions(channel)

        pain_points_text = (
            ", ".join(insights.get("pain_points", []))
            if insights.get("pain_points")
            else "general improvement"
        )

        additional_info = (
            f"\nAdditional context: {additional_context}"
            if additional_context
            else ""
        )

        prompt = f"""You are an expert cold outreach specialist. Generate a personalized, engaging {channel.value} message.

TARGET PERSON:
- Name: {profile.name}
- Role: {profile.role}
- Company: {profile.company}
- Industry: {profile.industry}
- Seniority: {profile.seniority_level}
- Skills: {', '.join(profile.skills[:5])}

COMMUNICATION STYLE:
{style_description}

OUTREACH INSTRUCTIONS FOR {channel.value.upper()}:
{channel_instructions}

PAIN POINTS TO ADDRESS:
{pain_points_text}

REQUIREMENTS:
1. Be specific and personalized - show you did research
2. Match the person's communication style exactly
3. Include a clear, compelling call-to-action
4. Keep it concise and natural
5. Avoid generic corporate language
6. Sound human and authentic{additional_info}

Generate ONLY the message content, no explanations or meta-commentary:"""

        return prompt

    def _describe_communication_style(
        self, style: CommunicationStyle, profile: UserProfile
    ) -> str:
        """Describe communication style for the LLM"""

        descriptions = {
            CommunicationStyle.FORMAL: "Very professional, uses formal language, no slang, structured sentences",
            CommunicationStyle.SEMI_FORMAL: "Professional but approachable, some casual touches, clear and organized",
            CommunicationStyle.CASUAL: "Conversational tone, uses everyday language, approachable",
            CommunicationStyle.VERY_CASUAL: "Very informal, uses slang, emojis, abbreviations, very relaxed",
            CommunicationStyle.MIXED: "Varies between professional and casual depending on context",
        }

        base_description = descriptions.get(
            style, "Mixed communication style"
        )

        details = []
        if profile.uses_emojis:
            details.append("Frequently uses emojis")
        if profile.uses_slang:
            details.append("Uses casual slang and abbreviations")
        if not profile.uses_abbreviations:
            details.append("Writes out full words, no abbreviations")

        extra = " | ".join(details) if details else ""
        return f"{base_description} {extra}"

    def _get_channel_instructions(self, channel: OutreachChannel) -> str:
        """Get specific instructions for each channel"""

        instructions = {
            OutreachChannel.EMAIL: "Write a professional but personalized email. Include: compelling subject line, personal greeting, relevant value proposition, specific CTA. Length: 150-200 words.",
            OutreachChannel.LINKEDIN_DM: "Write a LinkedIn-appropriate message. Be professional but friendly. LinkedIn users expect concise, direct messages. Length: 100-150 words.",
            OutreachChannel.WHATSAPP: "Write a friendly WhatsApp message. Can use 'Hi' or casual greeting. Can include emojis if profile uses them. Keep it short and conversational. Length: 50-100 words.",
            OutreachChannel.SMS: "Write a short SMS message. Very concise, direct, with clear CTA. Length: 50-80 words.",
            OutreachChannel.INSTAGRAM_DM: "Write an Instagram DM. Can be very casual, use emojis, engage with their visual content if mentioned. Length: 80-120 words.",
        }

        return instructions.get(
            channel, "Write a personalized message"
        )

    def _generate_email_subject(
        self, profile: UserProfile, insights: dict
    ) -> str:
        """Generate an email subject line"""

        subjects = [
            f"Quick question for {profile.name.split()[0]}",
            f"Idea for {profile.company}",
            f"{profile.name} - collaboration idea",
            f"Thought you'd find this interesting",
            f"Brief question about your work at {profile.company}",
        ]

        # Use first insight or default
        if insights.get("pain_points"):
            pain_point = insights["pain_points"][0]
            return f"How we help {profile.company} with {pain_point.lower()}"

        return subjects[
            hash(profile.name) % len(subjects)
        ]  # Deterministic selection

    def _extract_or_generate_cta(
        self, content: str, profile: UserProfile, channel: OutreachChannel
    ) -> str:
        """Extract or generate a call-to-action"""

        ctas = {
            OutreachChannel.EMAIL: [
                "Would love to hear your thoughts.",
                "Would you be open to a brief chat?",
                "Let me know if this resonates.",
                "Quick 15-minute call?",
            ],
            OutreachChannel.LINKEDIN_DM: [
                "Would you be open to connecting?",
                "Happy to discuss further.",
                "Let's connect!",
                "Would love your thoughts.",
            ],
            OutreachChannel.WHATSAPP: [
                "Interested in chatting?",
                "Let me know your thoughts!",
                "Thoughts?",
                "Open to discussing this?",
            ],
            OutreachChannel.SMS: [
                "Reply if interested?",
                "Interested?",
                "Let me know!",
            ],
            OutreachChannel.INSTAGRAM_DM: [
                "Love your content btw!",
                "Your recent post was 🔥",
                "Would love to collaborate!",
            ],
        }

        channel_ctas = ctas.get(channel, ["Let me know your thoughts."])
        return channel_ctas[hash(profile.name) % len(channel_ctas)]

    def _estimate_reply_rate(self, profile: UserProfile, content: str) -> float:
        """Estimate likelihood of reply based on content and profile"""

        score = 0.5  # Base score

        # Adjust based on seniority (harder to reach senior people)
        seniority_multipliers = {
            "junior": 0.8,
            "mid": 0.7,
            "senior": 0.6,
            "lead": 0.5,
            "founder": 0.4,
        }
        score *= seniority_multipliers.get(profile.seniority_level, 0.65)

        # Content quality signals
        if len(content) > 50:
            score *= 1.1
        if len(content) > 200:
            score *= 0.95  # Too long might reduce reply rate

        if profile.name.lower() in content.lower():
            score *= 1.15  # Personalization bonus

        if profile.company.lower() in content.lower():
            score *= 1.15  # Company mention bonus

        # Ensure within 0-1 range
        return min(1.0, max(0.1, score))
