"""
FastAPI application for Cold Outreach Engine
Main API endpoints and server setup
"""
import logging
import time
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

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Track application start time
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("=" * 50)
    logger.info("Starting Cold Outreach Engine")
    logger.info("=" * 50)

    # Startup
    success = await initialize_llm()
    if success:
        logger.info("✓ LLM initialized successfully")
    else:
        logger.warning("⚠ LLM initialization failed - some features may not work")

    yield

    # Shutdown
    logger.info("=" * 50)
    logger.info("Shutting down Cold Outreach Engine")
    logger.info("=" * 50)
    await shutdown_llm()
    logger.info("✓ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Offline LLM-Powered Hyper-Personalized Cold Outreach Engine",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
analyzer = ProfileAnalyzer()
message_generator = MessageGenerator()


# ==================== API ENDPOINTS ====================


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - redirects to frontend"""
    return {"message": "Cold Outreach Engine API is running", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
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
    """
    Analyze a social media profile and extract structured information

    Returns:
        UserProfile: Extracted and analyzed profile data
    """
    try:
        logger.info(
            f"Analyzing profile: {request.profile_url} from {request.platform.value}"
        )

        # Mock data extraction (in production, this would scrape actual profiles)
        profile_data = _extract_profile_data(request.profile_url, request.platform)

        # Analyze the profile
        profile = analyzer.analyze_linkedin_profile(profile_data)

        # Save to database
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
    """
    Generate personalized outreach messages for specified channels

    Returns:
        OutreachResponse: Generated messages and profile information
    """
    try:
        logger.info(f"Generating outreach messages for: {request.profile_url}")

        # Step 1: Analyze profile
        profile_data = _extract_profile_data(request.profile_url, request.platform)
        profile = analyzer.analyze_linkedin_profile(profile_data)

        # Step 2: Generate messages
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

        # Step 3: Save profile and track interaction
        db = get_database()
        profile_saved = db.save_profile(profile)

        # Track in background
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
    """
    Search stored profiles by name, company, or role

    Args:
        q: Search query
        limit: Maximum results to return

    Returns:
        List of matching profiles
    """
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
    """
    Get all profiles from a specific industry

    Returns:
        List of profiles in the industry
    """
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
    """
    Get database and application statistics

    Returns:
        Statistics about stored data and usage
    """
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
    """
    Export all stored profiles

    Returns:
        Path to exported file
    """
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


# ==================== UTILITY FUNCTIONS ====================

def _extract_linkedin_profile(url: str) -> dict:
    """Extract real LinkedIn profile data"""
    try:
        from bs4 import BeautifulSoup
        import requests
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        logger.info(f"Scraping LinkedIn profile: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract name
        name_elem = soup.find('h1', class_='text-heading-xlarge')
        name = name_elem.text.strip() if name_elem else "Professional"
        
        # Extract headline/role
        headline_elem = soup.find('div', class_='text-body-medium')
        headline = headline_elem.text.strip() if headline_elem else "Professional"
        
        # Extract about
        about_elem = soup.find('div', class_='show-more-less-text')
        about = about_elem.text.strip() if about_elem else ""
        
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
        }
    except Exception as e:
        logger.error(f"Error scraping LinkedIn: {e}")
        return {"error":404}
    
def _extract_github_profile(url: str) -> dict:
    """Extract real GitHub profile data using API"""
    try:
        import requests
        import re
        
        match = re.search(r'github\.com/([a-zA-Z0-9\-]+)', url)
        if not match:
            return _get_demo_profile()
        
        username = match.group(1)
        api_url = f"https://api.github.com/users/{username}"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
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
        }
    except Exception as e:
        logger.error(f"Error extracting GitHub profile: {e}")
        return {"error":200}
    
def _extract_profile_data(url: str, platform: SocialMediaPlatform) -> dict:
    """Extract real profile data from URL"""
    import re
    
    try:
        # Handle different URL formats
        if "linkedin.com" in url or platform == SocialMediaPlatform.LINKEDIN:
            return _extract_linkedin_profile(url)
        elif "github.com" in url or platform == SocialMediaPlatform.GITHUB:
            return _extract_github_profile(url)
        else:
            return {"error":200}
    except Exception as e:
        logger.error(f"Error extracting profile: {e}")
        return {"error":200}
    

# ==================== STATIC FILES ====================

frontend_path = settings.BASE_DIR / "frontend"

if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    logger.info(f"Mounted /static from {frontend_path}")


@app.get("/")
async def root():
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    return {"message": "Cold Outreach Engine API running", "docs": "/docs"}


@app.get("/chat")
async def chat_page():
    chat_path = frontend_path / "chat.html"
    if chat_path.exists():
        return FileResponse(chat_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Chat interface not found")


@app.get("/assets/{path:path}")
async def serve_assets(path: str):
    """Serve assets from frontend directory"""
    asset_path = frontend_path / "assets" / path
    if asset_path.exists():
        return FileResponse(asset_path)
    raise HTTPException(status_code=404, detail="Asset not found")


def run_server():
    """Run the FastAPI server"""
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
