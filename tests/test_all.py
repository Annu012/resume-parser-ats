import pytest
from src.resume_parser import extract_text_from_pdf
from src.ats_scorer import ATSScorer
from src.job_matcher import SimpleJobMatcher

def test_ats_scorer():
    scorer = ATSScorer()
    test_resume = "John Doe\njohn@email.com\n" + ("word " * 100)
    result = scorer.calculate_score(test_resume)
    assert 0 <= result['total_score'] <= 100
    print(f"✅ ATS Score: {result['total_score']}")

def test_job_matcher():
    matcher = SimpleJobMatcher()
    matcher.jobs = [
        {'title': 'Python Dev', 'company': 'TechCorp', 'description': 'Python JavaScript'},
    ]
    resume = "Python developer with JavaScript skills"
    matches = matcher.match_resume_to_jobs(resume)
    assert len(matches) > 0
    print(f"✅ Found {len(matches)} job matches")

if __name__ == "__main__":
    test_ats_scorer()
    test_job_matcher()
    print("\n✅ All tests passed!")