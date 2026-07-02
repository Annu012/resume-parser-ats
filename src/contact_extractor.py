"""Extract contact info: name, email, phone."""
import re
import spacy

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# Matches (123) 456-7890, 123-456-7890, 123.456.7890, +1 123 456 7890, etc.
PHONE_RE = re.compile(
    r"(?:\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"
)

_nlp = None


def _get_nlp():
    """Lazy-load spaCy model so importing this module doesn't require it upfront."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_lg")
        except OSError:
            _nlp = spacy.load("en_core_web_sm")
    return _nlp


def extract_email(text: str) -> str | None:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    match = PHONE_RE.search(text)
    return match.group(0) if match else None


def extract_name(text: str) -> str | None:
    """Best-effort name extraction: look at the first few lines for a PERSON entity.

    Resumes almost always put the candidate's name at the top, so restricting
    the NER search to the first ~300 characters avoids false positives from
    names of former employers, references, etc. mentioned later in the doc.
    """
    header = text.strip()[:300]
    doc = _get_nlp()(header)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()
    return None


def extract_contact_info(text: str) -> dict:
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
    }


if __name__ == "__main__":
    sample = """John A. Smith
    john.smith@email.com | (555) 123-4567
    Summary: Experienced software engineer..."""
    print(extract_contact_info(sample))
