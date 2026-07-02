from typing import List

class SimpleJobMatcher:
    """Match resumes with job descriptions"""
    
    def __init__(self, jobs_csv: str = None):
        self.jobs = []
        if jobs_csv:
            import pandas as pd
            self.jobs = pd.read_csv(jobs_csv).to_dict('records')
    
    def extract_keywords(self, text: str) -> set:
        """Extract keywords from text"""
        # Simple tokenization
        words = text.lower().split()
        # Filter short words and common words
        stop_words = {'the', 'a', 'and', 'or', 'is', 'in', 'at', 'to', 'for'}
        return {w for w in words if len(w) > 3 and w not in stop_words}
    
    def match_resume_to_jobs(self, resume_text: str, top_k: int = 5) -> List[dict]:
        """Find top K matching jobs"""
        resume_keywords = self.extract_keywords(resume_text)
        
        matches = []
        for job in self.jobs:
            job_keywords = self.extract_keywords(job['description'])
            
            # Calculate overlap
            overlap = len(resume_keywords & job_keywords)
            total = len(resume_keywords | job_keywords)
            
            similarity = overlap / (total + 1e-6) if total > 0 else 0
            
            matches.append({
                'title': job['title'],
                'company': job.get('company', 'Unknown'),
                'match_score': similarity
            })
        
        # Return top K
        return sorted(matches, key=lambda x: x['match_score'], reverse=True)[:top_k]

# Test with sample jobs
test_jobs = [
    {'title': 'Python Developer', 'company': 'TechCorp', 'description': 'We need Python JavaScript React AWS expert'},
    {'title': 'Data Scientist', 'company': 'DataInc', 'description': 'Machine Learning Python TensorFlow scikit-learn'},
    {'title': 'DevOps Engineer', 'company': 'CloudSys', 'description': 'Docker Kubernetes AWS CI/CD pipelines'},
]

matcher = SimpleJobMatcher()
matcher.jobs = test_jobs

test_resume = "Python AWS Docker Kubernetes JavaScript expert"
matches = matcher.match_resume_to_jobs(test_resume, top_k=3)

for m in matches:
    print(f"{m['title']} ({m['company']}): {m['match_score']:.2%}")