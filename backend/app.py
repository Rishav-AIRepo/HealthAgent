from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import structlog

from backend.db.database import engine
from backend.db import models
from backend.routes import upload, chat, insights, fitness, users
from backend.routes import auth, billing, trends, longitudinal, medications
from config.settings import get_settings

log = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting Healthcare Agent API v2.0")
    models.Base.metadata.create_all(bind=engine)
    yield
    log.info("Shutting down")


app = FastAPI(
    title="Healthcare + Fitness Agent API",
    description="AI-powered health analysis and fitness planning",
    version="2.0.0",
    lifespan=lifespan,
)

# SessionMiddleware must be added before CORS (outermost layer)
app.add_middleware(SessionMiddleware, secret_key=settings.app_secret_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# v1 routes
app.include_router(upload.router,   prefix="/upload",   tags=["Upload"])
app.include_router(chat.router,     prefix="/chat",     tags=["Chat"])
app.include_router(insights.router, prefix="/insights", tags=["Insights"])
app.include_router(fitness.router,  prefix="/fitness",  tags=["Fitness"])
app.include_router(users.router,    prefix="/users",    tags=["Users"])

# v2 routes
app.include_router(auth.router,         prefix="/auth",         tags=["Auth"])
app.include_router(billing.router,      prefix="/billing",      tags=["Billing"])
app.include_router(trends.router,       prefix="/trends",       tags=["Trends"])
app.include_router(longitudinal.router, prefix="/longitudinal", tags=["Longitudinal"])
app.include_router(medications.router,  prefix="/medications",  tags=["Medications"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}
