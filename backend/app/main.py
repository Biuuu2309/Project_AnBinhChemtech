import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import customers, internal_jobs, quotations
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.services.quotation_service import seed_customers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_customers(db)
    finally:
        db.close()
    logger.info("Database ready: %s", settings.database_url)
    yield


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(quotations.router)
app.include_router(internal_jobs.router)


@app.get("/health")
def health():
    return {"status": "ok"}
