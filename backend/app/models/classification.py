from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class Verdict(str, enum.Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"


class RejectionReason(str, enum.Enum):
    QURAN_CONTRADICTION = "quran_contradiction"
    HISTORICAL_CONTRADICTION = "historical_contradiction"
    LOGICAL_CONTRADICTION = "logical_contradiction"
    BROKEN_CHAIN = "broken_chain"
    WEAK_NARRATOR = "weak_narrator"
    FABRICATOR_NARRATOR = "fabricator_narrator"
    SECTARIAN_BIAS = "sectarian_bias"
    LEGENDARY_CONTENT = "legendary_content"
    INTERNAL_CONTRADICTION = "internal_contradiction"
    PARALLEL_NARRATION_CONFLICT = "parallel_narration_conflict"
    OTHER = "other"


class Classification(Base):
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True, index=True)
    hadith_id = Column(Integer, ForeignKey("hadiths.id"), nullable=False, unique=True, index=True)

    verdict = Column(SAEnum(Verdict), nullable=False, index=True)

    # Rejection details (null when accepted)
    rejection_reasons = Column(JSON)  # list of RejectionReason values
    quran_references = Column(JSON)   # list of {"surah": int, "ayah": int, "text": str}

    # AI-generated analysis
    ai_reasoning = Column(Text)
    chain_analysis = Column(Text)
    narrator_issues = Column(JSON)    # list of {"narrator": str, "issue": str}

    # Scores (0-100)
    chain_score = Column(Integer)
    content_score = Column(Integer)
    overall_score = Column(Integer)

    # Sahih Othmani book position (null if rejected)
    sahih_othmani_number = Column(Integer, unique=True, nullable=True)

    reviewed_by_human = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
