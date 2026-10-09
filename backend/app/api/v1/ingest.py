from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.hadith import Hadith
from app.schemas.hadith import IngestRequest
from app.services.sunnah_client import hadith_client, EDITION_MAP

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/")
def ingest_hadiths(req: IngestRequest, db: Session = Depends(get_db)):
    """Load hadiths from local JSON files and store in database."""
    collection = req.collection.value

    if collection not in EDITION_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"'{collection}' not available. Supported: {list(EDITION_MAP.keys())}",
        )

    try:
        all_hadiths = hadith_client.load_all_from_local(collection)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    added = 0
    skipped = 0
    limit = req.limit

    for normalized in all_hadiths:
        if added >= limit:
            break
        urn = normalized.get("urn")
        if urn and db.query(Hadith).filter(Hadith.urn == urn).first():
            skipped += 1
            continue
        db.add(Hadith(**normalized))
        added += 1

    db.commit()
    return {
        "added": added,
        "skipped": skipped,
        "collection": collection,
        "total_in_collection": len(all_hadiths),
    }


@router.get("/available")
def list_available_collections():
    return {
        "collections": list(EDITION_MAP.keys()),
        "note": "Data loaded from local files. Run scripts/download_hadiths.py to refresh.",
    }
