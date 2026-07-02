"""Extract work experience: job titles and date ranges.

Approach: resume text has no reliable universal structure, so we anchor on
date ranges (the most regular pattern across resumes) and pull the nearby
line as the likely job title/company. This is a heuristic, not a guarantee --
expect to tune it against your own resume formats.
"""
import re

MONTHS = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t)?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)

# Matches things like "January 2019 to March 2021", "01/2019 - 03/2021",
# "2019 - Present", "Jan 2020 - Current"
DATE_RANGE_RE = re.compile(
    rf"""
    (
        (?:{MONTHS}\.?\s+\d{{4}}|\d{{1,2}}/\d{{4}}|\d{{4}})
        \s*(?:to|-|–|—)\s*
        (?:{MONTHS}\.?\s+\d{{4}}|\d{{1,2}}/\d{{4}}|\d{{4}}|Present|Current)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def extract_date_ranges(text: str) -> list[str]:
    return [m.group(0).strip() for m in DATE_RANGE_RE.finditer(text)]


def extract_experience_entries(text: str) -> list[dict]:
    """Split the resume around date ranges and grab the surrounding line as title/context.

    Returns a list of {date_range, context} dicts. `context` is a heuristic
    guess at the job title/company -- review and refine per your data.
    """
    entries = []
    for match in DATE_RANGE_RE.finditer(text):
        start, end = match.span()
        # Grab a window of text around the date range as context
        window_start = max(0, start - 100)
        window_end = min(len(text), end + 100)
        context = text[window_start:window_end].replace("\n", " ").strip()
        entries.append({
            "date_range": match.group(0).strip(),
            "context": context,
        })
    return entries


if __name__ == "__main__":
    sample = """
    HR Administrator/Marketing Associate
    January 2019 to March 2021
    Company Name - City, State

    Handled recruitment and onboarding for a team of 30+ employees.
    """
    print(extract_date_ranges(sample))
    print(extract_experience_entries(sample))
