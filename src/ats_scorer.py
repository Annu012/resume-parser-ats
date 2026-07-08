class ATSScorer:
    """Calculate ATS compatibility score.

    FIX applied: self.issues was previously set once in __init__ and never
    reset, so when one ATSScorer instance is reused across a batch (as
    inference.py does), issues from resume #1 stayed in the list through
    resume #24. calculate_score() now resets self.issues at the start of
    every call.

    NOTE: total_score currently maxes out at 40 (format 20 + length 20).
    The README previously claimed a 100-point scale with keyword and
    readability scoring — those don't exist in this file. If you want the
    real 100-point scale, check_keywords() and check_readability() below
    are stubbed out for you to implement; until then, total_score honestly
    reports out of 40.
    """

    MAX_POSSIBLE_SCORE = 40  # format (20) + length (20). Update if you add checks below.

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

    def check_keywords(self, text: str, job_description: str | None) -> float:
        """NOT YET IMPLEMENTED. Returns 0 until built.

        Intended: compare resume text against job_description keyword
        overlap. Needs job_description to be passed in — calculate_score()
        doesn't currently accept one.
        """
        return 0

    def check_readability(self, text: str) -> float:
        """NOT YET IMPLEMENTED. Returns 0 until built.

        Intended: score based on action verbs, quantified achievements
        (numbers/percentages in bullet points), sentence length, etc.
        """
        return 0

    def calculate_score(self, resume_text: str, job_description: str | None = None) -> dict:
        """Calculate total ATS score"""
        self.issues = []  # FIX: reset per call instead of leaking across a batch

        format_score = self.check_format(resume_text)
        length_score = self.check_length(resume_text)
        keyword_score = self.check_keywords(resume_text, job_description)
        readability_score = self.check_readability(resume_text)

        total = format_score + length_score + keyword_score + readability_score

        return {
            "total_score": min(total, 100),
            "max_possible_score": self.MAX_POSSIBLE_SCORE + (
                # once keyword/readability are implemented, bump this via
                # their own max constants instead of hardcoding
                0
            ),
            "format_score": format_score,
            "length_score": length_score,
            "keyword_score": keyword_score,
            "readability_score": readability_score,
            "issues": self.issues,
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
    print(f"ATS Score: {result['total_score']}/{scorer.MAX_POSSIBLE_SCORE} (keyword+readability not yet implemented)")
    print(f"Issues: {result['issues']}")

    # Prove the state-leak bug is fixed: call again with a short resume,
    # confirm issues doesn't contain leftovers from the call above
    result2 = scorer.calculate_score("Too short.")
    assert len(result2["issues"]) == 1, f"Expected 1 issue, got {result2['issues']}"
    print(f"State-leak check passed: issues correctly reset -> {result2['issues']}")
