from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.hadith import Hadith
from app.models.classification import Classification, Verdict
from app.schemas.classification import ClassificationResponse, ClassifyRequest, BulkClassifyRequest
from app.services.validation_engine import validation_engine

router = APIRouter(prefix="/classifications", tags=["classifications"])


@router.post("/classify", response_model=ClassificationResponse)
def classify_hadith(req: ClassifyRequest, db: Session = Depends(get_db)):
    hadith = db.query(Hadith).filter(Hadith.id == req.hadith_id).first()
    if not hadith:
        raise HTTPException(status_code=404, detail="Hadith not found")
    classification = validation_engine.classify(hadith, db)
    return classification


@router.post("/bulk-classify")
def bulk_classify(req: BulkClassifyRequest, db: Session = Depends(get_db)):
    results = validation_engine.bulk_classify(db, collection=req.collection, limit=req.limit)
    accepted = sum(1 for r in results if r.verdict == Verdict.ACCEPTED)
    rejected = sum(1 for r in results if r.verdict == Verdict.REJECTED)
    return {
        "processed": len(results),
        "accepted": accepted,
        "rejected": rejected,
    }


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Classification).count()
    accepted = db.query(Classification).filter(Classification.verdict == Verdict.ACCEPTED).count()
    rejected = db.query(Classification).filter(Classification.verdict == Verdict.REJECTED).count()
    last_sahih_num = (
        db.query(Classification.sahih_othmani_number)
        .filter(Classification.sahih_othmani_number.isnot(None))
        .order_by(Classification.sahih_othmani_number.desc())
        .scalar()
    )
    return {
        "total_classified": total,
        "accepted": accepted,
        "rejected": rejected,
        "sahih_othmani_count": last_sahih_num or 0,
    }


@router.get("/sahih-othmani", response_model=list[ClassificationResponse])
def get_sahih_othmani(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    items = (
        db.query(Classification)
        .filter(Classification.verdict == Verdict.ACCEPTED)
        .order_by(Classification.sahih_othmani_number)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items
