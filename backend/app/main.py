"""
BoneVision FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings
from app.routers.analysis import router as analysis_router
from app.services.inference import model_instance

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("bonevision")


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=" * 60)
    logger.info("BoneVision API v%s starting up", settings.APP_VERSION)
    logger.info("Demo mode: %s", settings.DEMO_MODE)
    model_instance.load_model()
    logger.info(
        "Model status: demo=%s | architecture=%s | classes=%s",
        model_instance.demo_mode,
        model_instance.arch_name,
        model_instance.classes,
    )
    logger.info("=" * 60)
    yield
    # Shutdown
    logger.info("BoneVision API shutting down.")


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "**BoneVision** — AI-assisted knee X-ray screening for Osteoarthritis classification.\n\n"
        "> ⚠️ **Medical Disclaimer**: This tool is for research and screening support only. "
        "All results must be confirmed by a qualified healthcare professional. "
        "This is NOT a substitute for clinical diagnosis."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(analysis_router)


# ---------------------------------------------------------------------------
# Root route
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(413)
async def request_too_large(_: Request, exc: Exception):
    return JSONResponse(
        status_code=413,
        content={"detail": f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB} MB."},
    )


@app.exception_handler(500)
async def internal_error(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s: %s", request.url, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again."},
    )
