import json
from openai import OpenAI
from app.core.config import settings

SYSTEM_PROMPT = """You are an expert in Islamic hadith sciences (Ulum al-Hadith), Quranic studies, and Islamic history.
Your task is to evaluate hadith narrations according to strict scholarly criteria and produce a structured classification.

You must evaluate each hadith against ALL of the following criteria:

1. SANAD (Chain of Transmission):
   - Is the chain continuous (muttasil) or broken (munqati')?
   - Are all narrators identified and traceable?
   - Are there hidden defects (ilal)?

2. NARRATOR RELIABILITY (Rijal al-Hadith):
   - Assess each narrator's trustworthiness based on classical Jarh wa Ta'dil works
   - Flag: weak narrators, liars/fabricators, unknown narrators, narrators with sectarian bias
   - Flag: narrators who lived impossible overlapping lifespans

3. QURAN CONSISTENCY:
   - Does the hadith contradict any Quranic verse?
   - Does it add obligations or prohibitions not sanctioned by the Quran?
   - Does it contradict established Quranic principles (justice, mercy, monotheism)?

4. HISTORICAL CONSISTENCY:
   - Does it contradict established historical facts about early Islamic history?
   - Does it reference events, places, or people anachronistically?

5. LOGICAL CONSISTENCY:
   - Does it describe physically impossible events not supported by Quranic miracles?
   - Does it contradict established natural laws without Quranic basis?
   - Is it internally consistent?

6. PARALLEL NARRATIONS:
   - Does it contradict stronger, better-attested narrations on the same topic?
   - Is it isolated (gharib) without corroboration?

Respond ONLY with valid JSON matching this exact schema:
{
  "verdict": "accepted" | "rejected",
  "overall_score": <0-100, higher = more authentic>,
  "chain_score": <0-100>,
  "content_score": <0-100>,
  "chain_analysis": "<detailed analysis of the chain of narration>",
  "ai_reasoning": "<comprehensive scholarly justification for the verdict>",
  "rejection_reasons": [<only if rejected> "quran_contradiction" | "historical_contradiction" | "logical_contradiction" | "broken_chain" | "weak_narrator" | "fabricator_narrator" | "sectarian_bias" | "legendary_content" | "internal_contradiction" | "parallel_narration_conflict" | "other"],
  "narrator_issues": [{"narrator": "<name>", "issue": "<specific problem>"}],
  "quran_references": [{"surah": <int>, "ayah": <int>, "text": "<relevant text>"}]
}"""


class AIService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            key = settings.OPENAI_API_KEY.get_secret_value()
            if not key.strip():
                raise RuntimeError("OPENAI_API_KEY is required for AI generation")
            self._client = OpenAI(api_key=key, timeout=90)
        return self._client

    def classify_hadith(self, hadith_text: str, narrator_chain: str, collection: str, hadith_number: int) -> dict:
        user_message = f"""Please evaluate the following hadith:

**Collection**: {collection}
**Hadith Number**: {hadith_number}

**Chain of Narration (Sanad)**:
{narrator_chain or "Not provided / embedded in text"}

**Hadith Text (Matn)**:
{hadith_text}

Provide your scholarly evaluation as JSON."""

        message = self.client.responses.create(
            model=settings.OPENAI_TEXT_MODEL,
            max_output_tokens=8192,
            reasoning={"effort": "low"},
            store=False,
            text={"format": {"type": "json_object"}},
            instructions=SYSTEM_PROMPT,
            input=[{"role": "user", "content": user_message}],
        )

        if message.status != "completed" or not message.output_text.strip():
            raise RuntimeError("OpenAI did not return a complete classification")
        raw = message.output_text.strip()
        # Strip markdown code fences if the model wraps the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        if not isinstance(result, dict) or result.get("verdict") not in {"accepted", "rejected"}:
            raise ValueError("OpenAI returned an invalid classification object")
        for field in ("overall_score", "chain_score", "content_score"):
            value = result.get(field)
            if type(value) is not int or not 0 <= value <= 100:
                raise ValueError(f"OpenAI returned an invalid {field}")
        return result

    def generate_book_entry(self, hadith_text: str, classification: dict) -> str:
        """Generate a formatted entry for Sahih Othmani or the Rejected collection."""
        verdict = classification.get("verdict")
        if verdict == "accepted":
            prompt = f"Write a scholarly book entry for this accepted hadith. Include the text cleanly formatted and a brief authentication note.\n\nHadith: {hadith_text}\n\nReasoning: {classification.get('ai_reasoning')}"
        else:
            prompt = f"Write a scholarly rejection entry for this hadith. State the rejection reasons clearly and cite the evidence.\n\nHadith: {hadith_text}\n\nReasoning: {classification.get('ai_reasoning')}\nRejection reasons: {classification.get('rejection_reasons')}"

        message = self.client.responses.create(
            model=settings.OPENAI_TEXT_MODEL,
            max_output_tokens=4096,
            reasoning={"effort": "low"},
            store=False,
            input=[{"role": "user", "content": prompt}],
        )
        if message.status != "completed" or not message.output_text.strip():
            raise RuntimeError("OpenAI did not return a complete book entry")
        return message.output_text


ai_service = AIService()
