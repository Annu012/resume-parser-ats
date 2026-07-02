"""Orchestrator: run all extractors on a resume and return a structured result."""
from contact_extractor import extract_contact_info
from skills_extractor import extract_skills
from experience_extractor import extract_experience_entries
from education_extractor import extract_education
from classifier import predict_category


def parse_resume(text: str, model_path: str = None) -> dict:
    result = {
        "contact": extract_contact_info(text),
        "skills": extract_skills(text),
        "experience": extract_experience_entries(text),
        "education": extract_education(text),
    }
    try:
        result["predicted_category"] = predict_category(text, model_path)
    except FileNotFoundError:
        result["predicted_category"] = None  # run classifier.py to train first
    return result


if __name__ == "__main__":
    import sys, json
    with open(sys.argv[1], encoding="utf-8") as f:
        text = f.read()
    print(json.dumps(parse_resume(text), indent=2))
