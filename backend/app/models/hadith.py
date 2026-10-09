from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class Collection(str, enum.Enum):
    BUKHARI = "bukhari"
    MUSLIM = "muslim"
    MUWATTA = "malik"
    MUSNAD_AHMAD = "ahmed"
    ABU_DAWUD = "abudawud"
    TIRMIDHI = "tirmidhi"
    NASAI = "nasai"
    IBN_MAJAH = "ibnmajah"


class Hadith(Base):
    __tablename__ = "hadiths"

    id = Column(Integer, primary_key=True, index=True)

    # Source identifiers
    collection = Column(SAEnum(Collection), nullable=False, index=True)
    book_number = Column(Integer)
    hadith_number = Column(Integer)
    urn = Column(String(100), unique=True, index=True)

    # Content
    text_arabic = Column(Text)
    text_english = Column(Text, nullable=False)
    narrator_chain_raw = Column(Text)
    topics = Column(Text)

    # Traditional classification
    traditional_grade = Column(String(100))

    # Processing state
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
