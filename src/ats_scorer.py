class ATSScorer:
    """Calculate ATS compatibility score"""
    
    def __init__(self):
        self.score = 0
        self.issues = []
    
    def check_format(self, text: str) -> float:
        """Check if resume is ATS-friendly"""
        points = 0
        
        # No special characters
        if '©' not in text and '®' not in text:
            points += 5
        
        # Has clear sections
        sections = ['experience', 'education', 'skills', 'contact']
        found = sum(1 for s in sections if s.lower() in text.lower())
        points += (found / len(sections)) * 15
        
        return min(points, 20)
    
    def check_length(self, text: str) -> float:
        """Ideal length: 250-500 words"""
        word_count = len(text.split())
        
        if 250 <= word_count <= 500:
            return 20
        elif 200 <= word_count <= 600:
            return 15
        else:
            self.issues.append(f"Length: {word_count} words (ideal 250-500)")
            return 10
    
    def calculate_score(self, resume_text: str) -> dict:
        """Calculate total ATS score"""
        format_score = self.check_format(resume_text)
        length_score = self.check_length(resume_text)
        
        total = format_score + length_score  # Max 40 for now
        
        return {
            "total_score": min(total, 100),
            "format_score": format_score,
            "length_score": length_score,
            "issues": self.issues
        }

# Test
if __name__ == "__main__":
    test_resume = """
    John Doe
    john@email.com | (555) 123-4567
    
    EXPERIENCE
    Software Engineer at Tech Corp (2020-2023)
    - Led team of 5 developers
    - Improved performance by 40%
    - Deployed to 1M+ users
    
    EDUCATION
    BS Computer Science, State University (2020)
    
    SKILLS
    Python, JavaScript, React, AWS, Docker, Kubernetes
    """
    
    scorer = ATSScorer()
    result = scorer.calculate_score(test_resume)
    print(f"ATS Score: {result['total_score']}/100")
    print(f"Issues: {result['issues']}")