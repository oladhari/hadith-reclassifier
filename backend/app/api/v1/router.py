from fastapi import APIRouter
from app.api.v1 import hadith, classification, ingest

router = APIRouter()
router.include_router(hadith.router)
router.include_router(classification.router)
router.include_router(ingest.router)
