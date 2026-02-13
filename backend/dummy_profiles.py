"""
Dummy profiles for testing when real profiles fail to fetch
"""

DUMMY_PROFILES = {
    "john_doe": {
        "name": "John Doe",
        "email": "john.doe@techcorp.com",
        "role": "Senior Product Manager",
        "company": "TechCorp Inc",
        "industry": "Technology",
        "location": "San Francisco, CA",
        "bio": "Building AI products | Coffee enthusiast | Always learning",
        "about": "10+ years in product management. Passionate about user-centric design and data-driven decisions. Love leading cross-functional teams.",
        "skills": ["Product Management", "AI/ML", "Data Analysis", "Team Leadership", "Strategy"],
        "interests": ["AI", "Startups", "Product Design", "Coffee", "Travel"],
        "education": "MIT - Computer Science",
        "years_experience": 10,
        "profile_url": "https://linkedin.com/in/johndoe",
        "language": "english",
    },
    
    "sarah_sharma": {
        "name": "Sarah Sharma",
        "email": "sarah@startupxyz.com",
        "role": "Founder & CEO",
        "company": "StartupXYZ",
        "industry": "SaaS",
        "location": "New York, NY",
        "bio": "CEO @StartupXYZ | Building the future of collaboration 🚀",
        "about": "Founded StartupXYZ to help teams collaborate better. Experienced in fundraising, growth hacking, and scaling teams from 0 to 50+.",
        "skills": ["Fundraising", "Business Strategy", "Growth Hacking", "Leadership", "Sales"],
        "interests": ["Startups", "Venture Capital", "Entrepreneurship", "Networking"],
        "education": "Stanford - MBA",
        "years_experience": 8,
        "profile_url": "https://linkedin.com/in/sarah-sharma",
        "language": "english",
    },
    
    "alex_kumar": {
        "name": "Alex Kumar",
        "email": "alex.kumar@devstudio.com",
        "role": "Senior Software Engineer",
        "company": "DevStudio",
        "industry": "Technology",
        "location": "Bangalore, India",
        "bio": "Senior Eng @DevStudio | Python/Go enthusiast | Open source lover",
        "about": "8+ years building scalable systems. Love clean code, good architecture, and mentoring junior engineers. Active open source contributor.",
        "skills": ["Python", "Go", "Kubernetes", "System Design", "DevOps", "AWS"],
        "interests": ["Open Source", "System Design", "Cloud Architecture", "Performance Optimization"],
        "education": "IIT Delhi - Computer Science",
        "years_experience": 8,
        "profile_url": "https://github.com/alexkumar",
        "language": "english",
    },
    
    "emma_wilson": {
        "name": "Emma Wilson",
        "email": "emma.wilson@designstudio.io",
        "role": "Design Lead",
        "company": "Design Studio",
        "industry": "Design",
        "location": "London, UK",
        "bio": "Design Lead | UX/UI Enthusiast | User-centric design advocate",
        "about": "Passionate about creating beautiful and intuitive user experiences. Led design teams at multiple startups. Love collaborating with product and engineering.",
        "skills": ["UX/UI Design", "Figma", "User Research", "Design Systems", "Team Leadership"],
        "interests": ["Design Thinking", "User Experience", "Accessibility", "Design Tools"],
        "education": "Royal College of Art - Interaction Design",
        "years_experience": 6,
        "profile_url": "https://linkedin.com/in/emmawilson",
        "language": "english",
    },
    
    "michael_chen": {
        "name": "Michael Chen",
        "email": "michael@marketingpro.com",
        "role": "Marketing Director",
        "company": "Marketing Pro",
        "industry": "Marketing",
        "location": "Toronto, Canada",
        "bio": "Marketing Director | Growth Hacker | Data-driven marketer",
        "about": "15+ years in marketing and growth. Helped scale 5 companies from startup to Series B. Expert in product marketing and go-to-market strategy.",
        "skills": ["Marketing Strategy", "Growth Hacking", "Product Marketing", "Analytics", "Team Leadership"],
        "interests": ["Growth Marketing", "SaaS", "Content Marketing", "Community Building"],
        "education": "University of Toronto - Commerce",
        "years_experience": 15,
        "profile_url": "https://linkedin.com/in/michaelchen",
        "language": "english",
    },
    
    "lisa_patel": {
        "name": "Lisa Patel",
        "email": "lisa@venturesfund.com",
        "role": "Venture Capitalist",
        "company": "Ventures Fund",
        "industry": "Finance",
        "location": "Boston, MA",
        "bio": "VC at Ventures Fund | Investing in AI and Climate Tech",
        "about": "Invested in 50+ startups. Focus on early-stage AI, climate tech, and fintech. Former entrepreneur with 2 successful exits.",
        "skills": ["Venture Capital", "Investment Analysis", "Networking", "Startup Strategy", "Due Diligence"],
        "interests": ["AI", "Climate Tech", "Fintech", "Entrepreneurship"],
        "education": "Harvard Business School - MBA",
        "years_experience": 12,
        "profile_url": "https://linkedin.com/in/lisapatel",
        "language": "english",
    },
}


def get_dummy_profile(profile_id: str) -> dict:
    """Get a specific dummy profile by ID"""
    return DUMMY_PROFILES.get(profile_id.lower())


def get_random_dummy_profile() -> dict:
    """Get a random dummy profile"""
    import random
    profile_id = random.choice(list(DUMMY_PROFILES.keys()))
    return DUMMY_PROFILES[profile_id]


def get_all_dummy_profiles() -> dict:
    """Get all dummy profiles"""
    return DUMMY_PROFILES


def get_dummy_profile_names() -> list:
    """Get list of all dummy profile names for UI suggestions"""
    return list(DUMMY_PROFILES.keys())