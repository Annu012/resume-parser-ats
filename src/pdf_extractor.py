import PyPDF2
import spacy

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF resume"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def parse_resume(text: str) -> dict:
    """Parse resume using spaCy"""
    nlp = spacy.load("en_core_web_lg")
    doc = nlp(text)
    
    # Extract entities
    entities = {}
    for ent in doc.ents:
        if ent.label_ not in entities:
            entities[ent.label_] = []
        entities[ent.label_].append(ent.text)
    
    return entities

# Test it
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
        print("❌ No PDF files found. Download datasets first!")