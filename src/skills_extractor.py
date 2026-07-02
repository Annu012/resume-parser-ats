"""Extract skills by matching against a known skills taxonomy.

Keyword matching (vs. pure NER) is deliberate here: skills are open-vocabulary
and highly domain-specific, so a curated list + spaCy's PhraseMatcher gives
far more precise and controllable results than trying to train/rely on NER
for an entity type spaCy was never trained to recognize.
"""
import spacy
from spacy.matcher import PhraseMatcher

# Starter taxonomy -- expand this list with skills relevant to your target
# job categories. Consider loading from a CSV/JSON file as this grows.
SKILLS = [
    # Programming / tech
    "python", "java", "javascript", "typescript", "c++", "c#", "sql", "r",
    "html", "css", "react", "node.js", "django", "flask", "aws", "azure",
    "gcp", "docker", "kubernetes", "git", "linux", "machine learning",
    "deep learning", "data analysis", "data visualization", "excel",
    "tableau", "power bi", "pandas", "numpy", "tensorflow", "pytorch",
    # Business / soft skills
    "project management", "leadership", "communication", "team management",
    "customer service", "sales", "marketing", "negotiation",
    "strategic planning", "budgeting", "financial analysis",
    "conflict resolution", "problem solving", "time management",
    # Healthcare
    "patient care", "clinical research", "medical terminology", "hipaa",
    "nursing", "phlebotomy",
    # General office
    "microsoft office", "salesforce", "quickbooks", "sap",
]

_matcher = None
_nlp = None


def _get_matcher():
    global _matcher, _nlp
    if _matcher is None:
        try:
            _nlp = spacy.load("en_core_web_lg")
        except OSError:
            _nlp = spacy.load("en_core_web_sm")
        _matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")
        patterns = [_nlp.make_doc(skill) for skill in SKILLS]
        _matcher.add("SKILLS", patterns)
    return _matcher, _nlp


def extract_skills(text: str) -> list[str]:
    matcher, nlp = _get_matcher()
    doc = nlp(text)
    matches = matcher(doc)
    found = {doc[start:end].text.lower() for _, start, end in matches}
    return sorted(found)


if __name__ == "__main__":
    sample = "Experienced in Python, SQL, and Tableau. Strong leadership and project management skills."
    print(extract_skills(sample))
