from sqlalchemy import Column, Integer, String, Text, Enum as SAEnum
import enum

from app.core.database import Base


class NarratorReliability(str, enum.Enum):
    THIQAH = "thiqah"           # Reliable
    SADOOQ = "sadooq"           # Mostly reliable
    WEAK = "weak"
    VERY_WEAK = "very_weak"
    LIAR = "liar"               # Accused of fabrication
    UNKNOWN = "unknown"
    DISPUTED = "disputed"


class Narrator(Base):
    __tablename__ = "narrators"

    id = Column(Integer, primary_key=True, index=True)
    name_arabic = Column(String(500), nullable=False)
    name_transliterated = Column(String(500))
    death_year_ah = Column(Integer)
    reliability = Column(SAEnum(NarratorReliability), default=NarratorReliability.UNKNOWN)
    reliability_notes = Column(Text)
    sectarian_bias = Column(String(200))
    classical_judgments = Column(Text)
