from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.classification import Verdict, RejectionReason


class NarratorIssue(BaseModel):
    narrator: str
    issue: str


class QuranReference(BaseModel):
    surah: int
    ayah: int
    text: str


class ClassificationResponse(BaseModel):
    id: int
    hadith_id: int
    verdict: Verdict
    rejection_reasons: Optional[list[str]] = None
    quran_references: Optional[list[QuranReference]] = None
    ai_reasoning: Optional[str] = None
    chain_analysis: Optional[str] = None
    narrator_issues: Optional[list[NarratorIssue]] = None
    chain_score: Optional[int] = None
    content_score: Optional[int] = None
    overall_score: Optional[int] = None
    sahih_othmani_number: Optional[int] = None
    reviewed_by_human: bool
    created_at: datetime

    class Config:
        from_attributes = True


class HadithWithClassification(BaseModel):
    hadith: "HadithResponse"
    classification: Optional[ClassificationResponse] = None

    class Config:
        from_attributes = True


class ClassifyRequest(BaseModel):
    hadith_id: int


class BulkClassifyRequest(BaseModel):
    collection: Optional[str] = None
    limit: int = 10


# Resolve forward reference
from app.schemas.hadith import HadithResponse
HadithWithClassification.model_rebuild()
