"""Enhanced Resume Parser using Google Gemini (free tier)"""

import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional


class ExperienceItem(BaseModel):
    company: str
    title: str
    duration: str
    responsibilities: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)


class ResumeData(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[dict] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)


class GeminiResumeParser:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=model,
            temperature=0,
            max_output_tokens=2000
        )

    def parse_resume(self, resume_text: str) -> dict:
        prompt = PromptTemplate(
            input_variables=["resume_text"],
            template="""Extract structured information from this resume and return ONLY valid JSON.

Resume:
{resume_text}

Extract and return this exact JSON structure:
{{"name": "Full name", "email": "email@example.com", "phone": "+1234567890",
"summary": "Professional summary", "experience": [{{"company": "Company", "title": "Title",
"duration": "2020-2023", "responsibilities": [], "achievements": []}}],
"education": [{{"institution": "Uni", "degree": "BS", "field": "CS", "year": "2020"}}],
"skills": ["Skill1", "Skill2"], "certifications": ["Cert1"]}}

IMPORTANT: Return ONLY the JSON, no other text."""
        )

        response = self.llm.invoke(prompt.format(resume_text=resume_text))

        try:
            # Strip markdown code fences robustly (handles ```json ... ``` or plain ```...```)
            json_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.content.strip())

            parsed = json.loads(json_text)

            # Validate structure against the schema; raises if malformed
            validated = ResumeData(**parsed)

            return {"success": True, "data": validated.model_dump()}

        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON returned: {e}", "raw": response.content}
        except ValidationError as e:
            return {"success": False, "error": f"Schema validation failed: {e}", "raw": response.content}


# Test
if __name__ == "__main__":
    import os
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set. In PowerShell: $env:GOOGLE_API_KEY = \"your-key-here\"")
    else:
        parser = GeminiResumeParser(api_key)
        test_resume = "JOHN DOE\njohn@email.com\nPython Developer with 5 years experience"
        result = parser.parse_resume(test_resume)
        if result["success"]:
            print("✅ Parsed:", result["data"].get("name"))
        else:
            print("❌ Error:", result["error"])