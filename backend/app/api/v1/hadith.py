from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.hadith import Hadith, Collection
from app.models.classification import Classification
from app.schemas.hadith import HadithResponse, HadithListResponse
from app.schemas.classification import HadithWithClassification

router = APIRouter(prefix="/hadiths", tags=["hadiths"])


@router.get("/", response_model=HadithListResponse)
def list_hadiths(
    collection: Collection | None = None,
    search: str | None = Query(None, min_length=3),
    is_processed: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Hadith)
    if collection:
        query = query.filter(Hadith.collection == collection)
    if is_processed is not None:
        query = query.filter(Hadith.is_processed == is_processed)
    if search:
        query = query.filter(
            or_(
                Hadith.text_english.ilike(f"%{search}%"),
                Hadith.narrator_chain_raw.ilike(f"%{search}%"),
            )
        )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return HadithListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/{hadith_id}", response_model=HadithWithClassification)
def get_hadith(hadith_id: int, db: Session = Depends(get_db)):
    hadith = db.query(Hadith).filter(Hadith.id == hadith_id).first()
    if not hadith:
        raise HTTPException(status_code=404, detail="Hadith not found")
    classification = db.query(Classification).filter_by(hadith_id=hadith_id).first()
    return HadithWithClassification(hadith=hadith, classification=classification)
