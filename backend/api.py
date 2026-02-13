import logging
import time
import re
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from backend.config import settings
from backend.models import (
    OutreachRequest,
    OutreachResponse,
    UserProfile,
    HealthResponse,
    ErrorResponse,
    OutreachChannel,
    SocialMediaPlatform,
)
from backend.llm_handler import initialize_llm, shutdown_llm, get_llm_handler
from backend.profile_analyzer import ProfileAnalyzer
from backend.message_generator import MessageGenerator
from backend.database import get_database
from backend.dummy_profiles import get_dummy_profile, DUMMY_PROFILES

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("Starting Cold Outreach Engine")
    logger.info("=" * 50)

    success = await initialize_llm()
    if success:
        logger.info("✓ LLM initialized successfully")
    else:
        logger.warning("⚠ LLM initialization failed - some features may not work")

    yield

    logger.info("=" * 50)
    logger.info("Shutting down Cold Outreach Engine")
    logger.info("=" * 50)
    await shutdown_llm()
    logger.info("✓ Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="Offline LLM-Powered Hyper-Personalized Cold Outreach Engine",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = ProfileAnalyzer()
message_generator = MessageGenerator()


def _extract_linkedin_profile(url: str) -> Optional[dict]:
    """
    Try to extract real LinkedIn profile data.
    Returns None if fails (for fallback handling).
    """
    try:
        from bs4 import BeautifulSoup
        import requests
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        logger.info(f"Attempting to scrape LinkedIn: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        name_elem = soup.find('h1', class_='text-heading-xlarge')
        name = name_elem.text.strip() if name_elem else "Professional"
        
        headline_elem = soup.find('div', class_='text-body-medium')
        headline = headline_elem.text.strip() if headline_elem else "Professional"
        
        about_elem = soup.find('div', class_='show-more-less-text')
        about = about_elem.text.strip() if about_elem else ""
        
        logger.info(f"✓ Successfully scraped LinkedIn profile: {name}")
        
        return {
            "name": name,
            "role": headline,
            "company": headline.split(" at ")[-1] if " at " in headline else "",
            "about": about,
            "bio": headline,
            "profile_url": url,
            "skills": [],
            "interests": [],
            "education": "",
            "industry": "Technology",
            "location": "",
            "email": "",
            "years_experience": 5,
            "language": "english",
            "source": "linkedin_scraped",
        }
    except Exception as e:
        logger.warning(f"⚠️ Failed to scrape LinkedIn {url}: {str(e)}")
        logger.info(f"→ Will fallback to dummy data instead")
        return None

    
def _extract_github_profile(url: str) -> Optional[dict]:
    """
    Try to extract real GitHub profile data from API.
    Returns None if fails (for fallback handling).
    """
    try:
        import requests
        
        match = re.search(r'github\.com/([a-zA-Z0-9\-]+)', url)
        if not match:
            logger.warning(f"Invalid GitHub URL format: {url}")
            return None
        
        username = match.group(1)
        api_url = f"https://api.github.com/users/{username}"
        
        logger.info(f"Attempting to fetch GitHub profile: {username}")
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        logger.info(f"✓ Successfully fetched GitHub profile: {data.get('name', username)}")
        
        return {
            "name": data.get('name', username),
            "role": data.get('bio', 'Developer'),
            "company": data.get('company', ''),
            "about": "",
            "bio": data.get('bio', ''),
            "profile_url": url,
            "skills": ["Programming", "Development"],
            "interests": ["Open Source", "Coding"],
            "education": "",
            "industry": "Technology",
            "location": data.get('location', ''),
            "email": data.get('email', ''),
            "years_experience": 5,
            "language": "english",
            "source": "github_api",
        }
    except Exception as e:
        logger.warning(f"⚠️ Failed to fetch GitHub {url}: {str(e)}")
        logger.info(f"→ Will fallback to dummy data instead")
        return None


def _get_dummy_profile_fallback(url: str) -> dict:
    """
    Get random dummy profile as fallback when real profile fetch fails.
    """
    import random
    profile = random.choice(list(DUMMY_PROFILES.values())).copy()
    profile["source"] = "dummy_fallback"
    logger.info(f"📦 Using dummy profile (fallback): {profile.get('name')}")
    return profile


def _extract_profile_data(url: str, platform: SocialMediaPlatform) -> dict:
    """
    Extract profile data from URL with fallback to dummy data.
    
    Priority:
    1. Check if input matches dummy profile name
    2. Try to fetch from GitHub API
    3. Try to scrape LinkedIn
    4. Fallback to random dummy profile
    """
    
    logger.info(f"Processing profile: {url} (platform: {platform.value})")
    
    try:
        # PRIORITY 1: Check if user typed a dummy profile name
        dummy_profile = get_dummy_profile(url)
        if dummy_profile:
            logger.info(f"✓ Found dummy profile by name: {url}")
            dummy_copy = dummy_profile.copy()
            dummy_copy["source"] = "dummy_named"
            return dummy_copy
        
        # PRIORITY 2: Try GitHub
        if "github.com" in url or platform == SocialMediaPlatform.GITHUB:
            logger.info(f"Trying GitHub...")
            result = _extract_github_profile(url)
            if result:
                return result
            logger.warning(f"GitHub fetch failed, using dummy data")
            return _get_dummy_profile_fallback(url)
        
        # PRIORITY 3: Try LinkedIn
        if "linkedin.com" in url or platform == SocialMediaPlatform.LINKEDIN:
            logger.info(f"Trying LinkedIn...")
            result = _extract_linkedin_profile(url)
            if result:
                return result
            logger.warning(f"LinkedIn scrape failed, using dummy data")
            return _get_dummy_profile_fallback(url)
        
        # PRIORITY 4: Unknown URL format - use dummy
        logger.warning(f"Unknown URL format: {url}, using dummy data")
        return _get_dummy_profile_fallback(url)
        
    except Exception as e:
        logger.error(f"❌ Unexpected error processing profile: {e}")
        logger.info(f"Falling back to dummy data as safety measure")
        return _get_dummy_profile_fallback(url)


@app.get("/api/dummy-profiles", tags=["Testing"])
async def list_dummy_profiles():
    """Get list of available dummy profiles for testing"""
    profile_names = list(DUMMY_PROFILES.keys())
    return {
        "available_profiles": profile_names,
        "count": len(profile_names),
        "description": "Use these profile names in chat instead of URLs",
        "examples": profile_names[:3]
    }


@app.get("/", tags=["Root"])
async def root():
    index_path = settings.BASE_DIR / "frontend" / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    return {"message": "Cold Outreach Engine API is running", "docs": "/docs"}


@app.get("/chat", tags=["Root"])
async def chat_page():
    chat_path = settings.BASE_DIR / "frontend" / "chat.html"
    if chat_path.exists():
        return FileResponse(chat_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Chat interface not found")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    llm = get_llm_handler()
    uptime = time.time() - app_start_time

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        is_model_loaded=llm.is_loaded(),
        device=settings.DEVICE,
        uptime_seconds=uptime,
    )


@app.post("/api/analyze-profile", response_model=UserProfile, tags=["Profile"])
async def analyze_profile(request: OutreachRequest):
    try:
        logger.info(
            f"Analyzing profile: {request.profile_url} from {request.platform.value}"
        )

        profile_data = _extract_profile_data(request.profile_url, request.platform)

        profile = analyzer.analyze_linkedin_profile(profile_data)

        db = get_database()
        db.save_profile(profile)

        logger.info(f"✓ Profile analyzed and saved: {profile.name}")
        return profile

    except Exception as e:
        logger.error(f"Error analyzing profile: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error analyzing profile: {str(e)}"
        )


@app.post("/api/generate-outreach", response_model=OutreachResponse, tags=["Generation"])
async def generate_outreach(
    request: OutreachRequest, background_tasks: BackgroundTasks
):
    try:
        logger.info(f"Generating outreach messages for: {request.profile_url}")

        profile_data = _extract_profile_data(request.profile_url, request.platform)
        profile = analyzer.analyze_linkedin_profile(profile_data)

        messages = message_generator.generate_outreach_messages(
            profile=profile,
            channels=request.channels,
            additional_context=request.additional_context,
        )

        if not messages:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate messages",
            )

        db = get_database()
        profile_saved = db.save_profile(profile)

        background_tasks.add_task(
            db.save_interaction,
            profile.id or "",
            "outreach_generated",
            {"channels": [ch.value for ch in request.channels]},
        )

        logger.info(f"✓ Generated {len(messages)} messages")

        return OutreachResponse(
            profile=profile,
            messages=messages,
            profile_saved=profile_saved,
        )

    except Exception as e:
        logger.error(f"Error generating outreach: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating outreach: {str(e)}",
        )


@app.get("/api/profiles/search", tags=["Profile"])
async def search_profiles(q: str, limit: int = 10):
    try:
        db = get_database()
        profiles = db.search_profiles(q, limit)
        return {
            "query": q,
            "count": len(profiles),
            "profiles": profiles,
        }
    except Exception as e:
        logger.error(f"Error searching profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profiles/industry/{industry}", tags=["Profile"])
async def get_industry_profiles(industry: str, limit: int = 10):
    try:
        db = get_database()
        profiles = db.get_profiles_by_industry(industry, limit)
        return {
            "industry": industry,
            "count": len(profiles),
            "profiles": profiles,
        }
    except Exception as e:
        logger.error(f"Error getting profiles by industry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", tags=["Analytics"])
async def get_statistics():
    try:
        db = get_database()
        stats = db.get_database_stats()

        llm = get_llm_handler()

        return {
            **stats,
            "is_model_loaded": llm.is_loaded(),
            "model_name": settings.MODEL_NAME,
            "device": settings.DEVICE,
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profiles/export", tags=["Profile"])
async def export_profiles(format: str = "json"):
    try:
        db = get_database()
        export_path = db.export_profiles(format)

        return {
            "success": bool(export_path),
            "export_path": export_path,
            "format": format,
        }
    except Exception as e:
        logger.error(f"Error exporting profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


frontend_path = settings.BASE_DIR / "frontend"

if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    logger.info(f"Mounted /static from {frontend_path}")


def run_server():
    logger.info(f"Starting server on http://{settings.HOST}:{settings.PORT}")
    logger.info(f"Docs available at http://{settings.HOST}:{settings.PORT}/docs")

    uvicorn.run(
        "backend.api:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    run_server()