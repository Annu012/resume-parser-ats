"""
FastAPI backend exposing the resume parser as a real REST API.

Run with: uvicorn api:app --reload
Then visit http://127.0.0.1:8000/docs for interactive API docs.

Requires GOOGLE_API_KEY set in the environment for the LLM side of /parse
to work — without it, /parse still runs but returns NER-only results
(name/email/phone via contact_extractor.py; experience/education/skills
will be empty, since only Gemini currently supplies those).

/match-jobs is NOT wired yet — job_matcher.py hasn't been reviewed, so
rather than guess at its interface, this endpoint returns 501 until you
share that file too.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import tempfile
import os

from src.resume_parser import ResumeParser
from src.contact_extractor import extract_contact_info
from src.gemini_parser import GeminiResumeParser
from src.ats_scorer import ATSScorer
from src.hybrid_merger import normalize_extraction, merge_extractions

app = FastAPI(
    title="Resume Parser & ATS Optimizer API",
    description="Parses resumes via hybrid NER+LLM extraction and scores ATS compatibility.",
    version="0.2.0",
)

# Loaded once at startup, reused across requests
_parser = ResumeParser()
_scorer = ATSScorer()
_gemini_key = os.getenv("GOOGLE_API_KEY")
_llm_parser = GeminiResumeParser(_gemini_key) if _gemini_key else None


class ParsedResume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    experience: list | None = None
    education: list | None = None
    skills: list | None = None
    source_breakdown: dict | None = None  # which source won each field, for transparency


class ATSScoreRequest(BaseModel):
    resume_text: str
    job_description: str | None = None  # accepted but not yet used — see ats_scorer.py


class ATSScoreResponse(BaseModel):
    total_score: float
    max_possible_score: int
    format_score: float
    length_score: float
    keyword_score: float
    readability_score: float
    issues: list[str]


@app.post("/parse", response_model=ParsedResume)
async def parse_resume(file: UploadFile = File(...)):
    """Upload a resume PDF, get back hybrid NER+LLM extracted fields."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        text = _parser.extract_text_from_pdf(tmp_path)

        ner_result = normalize_extraction(extract_contact_info(text), source="ner")

        llm_result = {}
        if _llm_parser is not None:
            llm_raw = _llm_parser.parse_resume(text)
            if llm_raw.get("success"):
                llm_result = normalize_extraction(llm_raw["data"], source="llm")

        hybrid = merge_extractions(ner_result, llm_result)

        return ParsedResume(
            name=hybrid.get("name", {}).get("value"),
            email=hybrid.get("email", {}).get("value"),
            phone=hybrid.get("phone", {}).get("value"),
            experience=hybrid.get("experience", {}).get("value"),
            education=hybrid.get("education", {}).get("value"),
            skills=hybrid.get("skills", {}).get("value"),
            source_breakdown={k: v.get("source") for k, v in hybrid.items()},
        )
    finally:
        os.unlink(tmp_path)


@app.post("/ats-score", response_model=ATSScoreResponse)
async def ats_score(req: ATSScoreRequest):
    """Score a resume's ATS compatibility. Currently out of 40 — see ats_scorer.py."""
    result = _scorer.calculate_score(req.resume_text, req.job_description)
    return ATSScoreResponse(**result)


@app.post("/match-jobs")
async def match_jobs():
    raise HTTPException(
        501,
        "Not wired yet — job_matcher.py hasn't been reviewed. "
        "Share its contents to finish this endpoint.",
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "llm_enabled": _llm_parser is not None,
    }
