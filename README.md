# Resume Parser & ATS Optimizer

## Week 1 Progress
- ✅ Resume PDF extraction working
- ✅ ATS compatibility scoring (0-100)
- ✅ Job matching engine
- ✅ Streamlit web interface
- ✅ Unit tests passing

## Metrics (to be updated)
- Parsing accuracy: TBD
- ATS score prediction: TBD
- Processing time: <3 seconds per resume

## Next Steps (Week 2)
- Integrate OpenAI for semantic parsing
- Expand job matching with embeddings
- Collect and annotate 100+ resumes
- Improve accuracy to 90%+

## How to Run
bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

streamlit run app_simple.py


## Files
- `src/resume_parser.py`: PDF extraction + spaCy NER
- `src/ats_scorer.py`: ATS compatibility scoring
- `src/job_matcher.py`: Job matching logic
- `app_simple.py`: Streamlit UI
- `tests/`: Test suite