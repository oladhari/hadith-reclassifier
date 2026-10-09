from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.hadith import Collection


class HadithBase(BaseModel):
    collection: Collection
    book_number: Optional[int] = None
    hadith_number: Optional[int] = None
    urn: Optional[str] = None
    text_arabic: Optional[str] = None
    text_english: str
    narrator_chain_raw: Optional[str] = None
    topics: Optional[str] = None
    traditional_grade: Optional[str] = None


class HadithCreate(HadithBase):
    pass


class HadithResponse(HadithBase):
    id: int
    is_processed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class HadithListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[HadithResponse]


class IngestRequest(BaseModel):
    collection: Collection
    limit: int = 50
