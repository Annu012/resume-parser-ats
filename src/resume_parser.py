from pypdf import PdfReader
import spacy


def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from PDF resume. Accepts a file path (str) or a file-like object."""
    if isinstance(pdf_file, str):
        with open(pdf_file, 'rb') as file:
            reader = PdfReader(file)
            text = "".join(page.extract_text() or "" for page in reader.pages)
    else:
        reader = PdfReader(pdf_file)
        text = "".join(page.extract_text() or "" for page in reader.pages)
    return text


def parse_resume(text: str) -> dict:
    """Parse resume using spaCy, returns dict of entity_label -> list of entity strings."""
    nlp = spacy.load("en_core_web_lg")
    doc = nlp(text)

    entities = {}
    for ent in doc.ents:
        if ent.label_ not in entities:
            entities[ent.label_] = []
        entities[ent.label_].append(ent.text)

    return entities


class ResumeParser:
    """Class wrapper around the module-level parsing functions, for pipeline-style usage."""

    def __init__(self):
        # Load spaCy once at construction time, rather than on every call,
        # since nlp.load() is relatively expensive.
        self.nlp = spacy.load("en_core_web_lg")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        return extract_text_from_pdf(pdf_path)

    def extract_entities(self, text: str) -> dict:
        doc = self.nlp(text)
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
        return entities


# Test
if __name__ == "__main__":
    pdf_files = __import__('glob').glob("data/raw/*.pdf")

    if pdf_files:
        test_pdf = pdf_files[0]
        print(f"Testing with: {test_pdf}")

        text = extract_text_from_pdf(test_pdf)
        print(f"Extracted {len(text)} characters")

        entities = parse_resume(text)
        print(f"Found entities: {list(entities.keys())}")
    else:
        print("No PDF files found in data/raw/")