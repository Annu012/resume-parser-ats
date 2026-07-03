"""Advanced Job Matching with Similarity"""

from typing import List, Dict

class AdvancedJobMatcher:
    def __init__(self, jobs_data: List[Dict] = None):
        self.jobs = jobs_data or []
    
    def _extract_keywords(self, text: str) -> set:
        stop_words = {'the', 'a', 'and', 'or', 'in', 'on', 'at', 'to', 'for'}
        words = text.lower().split()
        return {w for w in words if len(w) > 3 and w not in stop_words and w.isalpha()}
    
    def match_resume_to_jobs(self, resume_text: str, resume_skills: List[str], top_k: int = 5) -> List[Dict]:
        resume_keywords = self._extract_keywords(resume_text)
        resume_skills = set(s.lower() for s in resume_skills)
        
        matches = []
        for job_id, job in enumerate(self.jobs):
            job_keywords = self._extract_keywords(job.get("description", ""))
            job_skills = set(s.lower() for s in job.get("required_skills", []))
            
            keyword_overlap = len(resume_keywords & job_keywords)
            max_keywords = max(len(resume_keywords), len(job_keywords))
            keyword_score = keyword_overlap / (max_keywords + 1e-6)
            
            skill_overlap = len(resume_skills & job_skills)
            max_skills = max(len(resume_skills), len(job_skills))
            skill_score = skill_overlap / (max_skills + 1e-6) if max_skills > 0 else 0
            
            final_score = (0.7 * skill_score) + (0.3 * keyword_score)
            
            matches.append({
                "job_id": job_id,
                "title": job.get("title"),
                "company": job.get("company"),
                "match_score": final_score
            })
        
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches[:top_k]

# Test
if __name__ == "__main__":
    sample_jobs = [
        {"title": "Python Dev", "company": "TechCorp", "description": "Python AWS Docker", "required_skills": ["Python", "AWS"]},
        {"title": "Data Scientist", "company": "DataInc", "description": "Python Machine Learning", "required_skills": ["Python", "ML"]}
    ]
    
    matcher = AdvancedJobMatcher(sample_jobs)
    matches = matcher.match_resume_to_jobs("Python developer", ["Python", "AWS"])
    
    for match in matches:
        print(f"{match['title']}: {match['match_score']:.2%}")