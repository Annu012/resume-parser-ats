"""
Hybrid merge logic for combining NER-based extraction (spaCy / your rule-based
extractors) with LLM-based extraction (GPT-4 / Gemini / Grok) into one result.

This is the piece that was missing: your NER extractors and LLM parsers run
independently, but nothing combines them into a single "hybrid" answer.

DESIGN
------
For each field (name, email, phone, experience, education, skills), each
source (ner, llm) proposes a value + a confidence score. The merger picks
a winner per field using simple, explainable rules — not a black box.

You control confidence per source. If your extractors don't currently return
confidence scores, start with the DEFAULT_SOURCE_CONFIDENCE below (rough
priors) and refine them once you have real eval data from evaluate.py.

INPUT FORMAT EXPECTED
----------------------
Each source's extraction should be normalized into this shape before merging:

    {
        "name":       {"value": "Anisa Shaikh", "confidence": 0.9},
        "email":      {"value": "a@x.com",      "confidence": 0.95},
        "phone":      {"value": "+91...",       "confidence": 0.8},
        "experience": {"value": [...],          "confidence": 0.7},
        "education":  {"value": [...],          "confidence": 0.75},
        "skills":     {"value": [...],          "confidence": 0.6},
    }

If your extractors currently return raw values with no confidence, wrap them:
    normalize_extraction(raw_dict, default_confidence=0.7)

USAGE
-----
    from src.hybrid_merger import merge_extractions

    ner_result = normalize_extraction(ner_extractor_output, default_confidence=0.65)
    llm_result = normalize_extraction(llm_parser_output, default_confidence=0.85)

    hybrid = merge_extractions(ner_result, llm_result)
    # hybrid["name"]["value"] -> the winning value
    # hybrid["name"]["source"] -> "ner" or "llm" or "agreement"
    # hybrid["name"]["confidence"] -> the confidence of the winning value
"""

from typing import Any

FIELDS = ["name", "email", "phone", "experience", "education", "skills"]

# Rough starting priors — NER tends to be more reliable on short, structured
# fields (email, phone); LLMs tend to be better on fields needing context
# (experience, education, skills). Replace these once evaluate.py gives you
# real per-field accuracy numbers instead of guessing.
DEFAULT_SOURCE_CONFIDENCE = {
    "ner": {
        "name": 0.85, "email": 0.9, "phone": 0.85,
        "experience": 0.6, "education": 0.65, "skills": 0.55,
    },
    "llm": {
        "name": 0.9, "email": 0.85, "phone": 0.8,
        "experience": 0.85, "education": 0.8, "skills": 0.8,
    },
}


def normalize_extraction(
    raw: dict[str, Any],
    source: str = "unknown",
    default_confidence: float | None = None,
) -> dict[str, dict]:
    """
    Wrap a raw {field: value} dict from an extractor into the
    {field: {"value": ..., "confidence": ...}} shape merge_extractions expects.

    If the extractor already returns confidence per field, pass those in raw
    as {field: {"value": ..., "confidence": ...}} and this passes it through.
    """
    normalized = {}
    for field in FIELDS:
        if field not in raw or raw[field] in (None, "", []):
            continue

        entry = raw[field]
        if isinstance(entry, dict) and "value" in entry:
            normalized[field] = {
                "value": entry["value"],
                "confidence": entry.get(
                    "confidence",
                    default_confidence
                    or DEFAULT_SOURCE_CONFIDENCE.get(source, {}).get(field, 0.7),
                ),
            }
        else:
            normalized[field] = {
                "value": entry,
                "confidence": default_confidence
                or DEFAULT_SOURCE_CONFIDENCE.get(source, {}).get(field, 0.7),
            }
    return normalized


def _values_agree(a: Any, b: Any) -> bool:
    """Loose equality check — case/whitespace-insensitive for strings."""
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().lower() == b.strip().lower()
    return a == b


def merge_extractions(
    ner_result: dict[str, dict],
    llm_result: dict[str, dict],
) -> dict[str, dict]:
    """
    Merge two normalized extraction dicts into one hybrid result.

    Rule per field:
      - If only one source has the field, use it.
      - If both sources agree on the value, use it with boosted confidence
        (agreement is itself signal).
      - If they disagree, take the higher-confidence value, and record the
        alternative for debugging/audit.
    """
    hybrid = {}

    for field in FIELDS:
        ner_entry = ner_result.get(field)
        llm_entry = llm_result.get(field)

        if ner_entry and not llm_entry:
            hybrid[field] = {**ner_entry, "source": "ner"}
        elif llm_entry and not ner_entry:
            hybrid[field] = {**llm_entry, "source": "llm"}
        elif ner_entry and llm_entry:
            if _values_agree(ner_entry["value"], llm_entry["value"]):
                boosted = min(1.0, max(ner_entry["confidence"], llm_entry["confidence"]) + 0.05)
                hybrid[field] = {
                    "value": llm_entry["value"],
                    "confidence": round(boosted, 3),
                    "source": "agreement",
                }
            else:
                winner, loser = (
                    (llm_entry, ner_entry)
                    if llm_entry["confidence"] >= ner_entry["confidence"]
                    else (ner_entry, llm_entry)
                )
                winner_source = "llm" if winner is llm_entry else "ner"
                hybrid[field] = {
                    "value": winner["value"],
                    "confidence": winner["confidence"],
                    "source": winner_source,
                    "disagreement_alternative": loser["value"],
                }
        # if neither source has the field, leave it out of hybrid

    return hybrid


if __name__ == "__main__":
    # Quick smoke test with fabricated example inputs — NOT real resume data,
    # just here to prove the merge logic runs correctly.
    example_ner = normalize_extraction(
        {"name": "Anisa Shaikh", "email": "anisa@example.com", "skills": ["Python", "React"]},
        source="ner",
    )
    example_llm = normalize_extraction(
        {"name": "Anisa Shaikh", "email": "a.shaikh@example.com",
         "skills": ["Python", "React", "FastAPI"], "experience": "3 years"},
        source="llm",
    )

    result = merge_extractions(example_ner, example_llm)
    import json
    print(json.dumps(result, indent=2))
