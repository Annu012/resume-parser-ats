"""Extract education info: degree and institution.

This dataset (and many PDF-derived resume texts) preserves original layout
via runs of whitespace where columns/sections used to be. Rather than
scanning the whole document for degree keywords (which produces false
positives on short abbreviations like "MA" or "AS"), this extractor:

  1. Isolates the actual Education section using section-header boundaries
     (headers are surrounded by 3+ spaces in this format).
  2. Splits that section into fields on 3+-space runs.
  3. Classifies each field as a degree, institution, date, or noise, using
     the "－" separator (which consistently precedes "City, State" in this
     dataset) as an anchor for institution names.

This is tuned to the layout quirks of PDF-to-text converted resumes and may
need adjustment for differently-formatted source documents.
"""
import re

SECTION_HEADERS = [
    "Summary", "Highlights", "Accomplishments", "Experience",
    "Education and Training", "Education", "Skills", "Certifications",
    "Additional Information", "Professional Affiliations", "Interests",
    "Objective", "Qualifications", "Professional Summary", "Career Overview",
]

_SECTION_PATTERN = re.compile(
    r"(?:(?<=\s{3})|^)(" + "|".join(SECTION_HEADERS) + r")(?=\s{3,})"
)

DEGREE_KEYWORDS = re.compile(
    r"""^(
        Bachelor(?:'?s)?(?:\s+of\s+\w+)? |
        Master(?:'?s)?(?:\s+of\s+\w+)? |
        Associate(?:'?s)?(?:\s+of\s+\w+)? |
        Doctor(?:ate)? | Ph\.?D\.? |
        MBA | M\.?B\.?A\.? |
        High\s+School\s+Diploma |
        Diploma | Certificate |
        B\.?S\.? | B\.?A\.? | M\.?S\.? | M\.?A\.? | A\.?S\.? | A\.?A\.? |
        B\.?Com\.? | B\.?L\.?I\.?S\.?
    )\s*:?\s*$""",
    re.IGNORECASE | re.VERBOSE,
)

# Fallback signal: a field naming an institution, independent of which
# separator character (if any) the source document used ("－", "-", ",").
INSTITUTION_KEYWORDS = re.compile(
    r"(University|College|Institute|Academy|School)", re.IGNORECASE
)

SEPARATOR_TOKENS = {"－", "-", "–", "—"}


def _get_section(text: str, name: str) -> str | None:
    matches = list(_SECTION_PATTERN.finditer(text))
    for i, m in enumerate(matches):
        if m.group(1) == name:
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            return text[start:end].strip()
    return None


def _find_education_section(text: str) -> str | None:
    """Try the more specific header variant first, then the generic one."""
    return _get_section(text, "Education and Training") or _get_section(text, "Education")


def extract_education(text: str) -> dict:
    section = _find_education_section(text)
    if not section:
        return {"degrees": [], "institutions": [], "raw_section": None}

    # Split on 3+ spaces (this dataset's usual column separator) AND newlines,
    # since a handful of resumes wrap education entries onto new lines instead.
    fields = [f.strip(" ,:") for f in re.split(r"\s{3,}|\n", section) if f.strip(" ,:")]

    degrees = []
    institutions = []

    for i, field in enumerate(fields):
        if field in SEPARATOR_TOKENS:
            # The field right before a dash-like separator is the institution
            if i > 0 and fields[i - 1] not in institutions:
                institutions.append(fields[i - 1])
        elif DEGREE_KEYWORDS.match(field) and field not in degrees:
            degrees.append(field)
        elif (
            INSTITUTION_KEYWORDS.search(field)
            and len(field.split()) <= 8
            and field not in institutions
        ):
            # Catches institutions named without a following separator token,
            # e.g. "Lamar University  ,   City" where the comma isn't a
            # field-splitting delimiter but "University" is a clear signal.
            # The word-count cap filters out narrative sentences that merely
            # mention "college"/"university" in passing.
            institutions.append(field)

    return {
        "degrees": degrees,
        "institutions": institutions,
        "raw_section": section,  # kept for manual review / debugging
    }


if __name__ == "__main__":
    sample = """
    Education     2014     Master of Arts  :   Corporate Communication & Public Relations
    Sacred Heart University   －   City  ,   State
    """
    print(extract_education(sample))
