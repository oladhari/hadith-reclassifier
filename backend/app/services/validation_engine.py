from sqlalchemy.orm import Session
from app.models.hadith import Hadith
from app.models.classification import Classification, Verdict
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)


class ValidationEngine:
    def classify(self, hadith: Hadith, db: Session) -> Classification:
        """Run AI classification on a hadith and persist the result."""
        existing = db.query(Classification).filter_by(hadith_id=hadith.id).first()
        if existing:
            return existing

        try:
            result = ai_service.classify_hadith(
                hadith_text=hadith.text_english,
                narrator_chain=hadith.narrator_chain_raw or "",
                collection=hadith.collection.value,
                hadith_number=hadith.hadith_number or 0,
            )
        except Exception as exc:
            logger.error(f"AI classification failed for hadith {hadith.id}: {exc}")
            raise

        classification = Classification(
            hadith_id=hadith.id,
            verdict=Verdict(result["verdict"]),
            overall_score=result.get("overall_score"),
            chain_score=result.get("chain_score"),
            content_score=result.get("content_score"),
            chain_analysis=result.get("chain_analysis"),
            ai_reasoning=result.get("ai_reasoning"),
            rejection_reasons=result.get("rejection_reasons"),
            narrator_issues=result.get("narrator_issues"),
            quran_references=result.get("quran_references"),
        )

        # Assign Sahih Othmani number if accepted
        if classification.verdict == Verdict.ACCEPTED:
            last = (
                db.query(Classification)
                .filter(Classification.sahih_othmani_number.isnot(None))
                .order_by(Classification.sahih_othmani_number.desc())
                .first()
            )
            classification.sahih_othmani_number = (last.sahih_othmani_number + 1) if last else 1

        db.add(classification)
        hadith.is_processed = True
        db.commit()
        db.refresh(classification)
        return classification

    def bulk_classify(self, db: Session, collection: str | None = None, limit: int = 10) -> list[Classification]:
        query = db.query(Hadith).filter(Hadith.is_processed == False)
        if collection:
            query = query.filter(Hadith.collection == collection)
        hadiths = query.limit(limit).all()

        results = []
        for hadith in hadiths:
            try:
                cls = self.classify(hadith, db)
                results.append(cls)
            except Exception as exc:
                logger.error(f"Skipping hadith {hadith.id}: {exc}")
        return results


validation_engine = ValidationEngine()
