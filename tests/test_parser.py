import pytest
from src.resume_parser import extract_text_from_pdf

def test_pdf_extraction():
    """Test PDF extraction works"""
    import glob
    pdfs = glob.glob("data/raw/*.pdf")
    
    if pdfs:
        text = extract_text_from_pdf(pdfs[0])
        assert len(text) > 0
        assert isinstance(text, str)
    else:
        pytest.skip("No PDF files available")

if __name__ == "__main__":
    test_pdf_extraction()
    print("✅ Test passed!")