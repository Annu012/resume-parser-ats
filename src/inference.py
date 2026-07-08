

import time
import glob
import json
import os
from pathlib import Path

from src.resume_parser import ResumeParser
from src.contact_extractor import extract_contact_info
from src.gemini_parser import GeminiResumeParser
from src.ats_scorer import ATSScorer
from src.hybrid_merger import normalize_extraction, merge_extractions


class ResumeParsingPipeline:
    def __init__(self, gemini_api_key: str | None = None):
        self.parser = ResumeParser()
        self.scorer = ATSScorer()

        gemini_api_key = gemini_api_key or os.getenv("GOOGLE_API_KEY")
        if gemini_api_key:
            self.llm_parser = GeminiResumeParser(gemini_api_key)
        else:
            self.llm_parser = None
            print(
                "WARNING: GOOGLE_API_KEY not set — pipeline will run NER-only. "
                "Set GOOGLE_API_KEY to enable the LLM side and make this "
                "genuinely hybrid."
            )

    def _ner_side(self, text: str) -> dict:
        """NER-side extraction. Currently only name/email/phone via
        contact_extractor.py. See module docstring re: the three unwired
        extractor files."""
        contact = extract_contact_info(text)
        return normalize_extraction(contact, source="ner")

    def _llm_side(self, text: str) -> dict:
        """LLM-side extraction via Gemini. Returns {} if no API key or if
        Gemini's response failed validation (see gemini_parser.py)."""
        if self.llm_parser is None:
            return {}
        result = self.llm_parser.parse_resume(text)
        if not result.get("success"):
            return {}
        return normalize_extraction(result["data"], source="llm")

    def process_resume(self, pdf_path: str) -> dict:
        start = time.time()
        try:
            text = self.parser.extract_text_from_pdf(pdf_path)

            ner_result = self._ner_side(text)
            llm_result = self._llm_side(text)
            hybrid = merge_extractions(ner_result, llm_result)

            ats_result = self.scorer.calculate_score(text)

            return {
                "file": Path(pdf_path).name,
                "extraction_time": time.time() - start,
                "hybrid_fields": hybrid,
                "ner_field_count": len(ner_result),
                "llm_field_count": len(llm_result),
                "ats_score": ats_result["total_score"],
                "ats_max_possible": ats_result["max_possible_score"] if "max_possible_score" in ats_result else None,
                "success": True,
                "error": None,
            }
        except Exception as e:
            return {
                "file": Path(pdf_path).name,
                "extraction_time": time.time() - start,
                "hybrid_fields": {},
                "ner_field_count": 0,
                "llm_field_count": 0,
                "ats_score": None,
                "ats_max_possible": None,
                "success": False,
                "error": str(e),
            }

    def process_batch(self, folder: str = "data/raw") -> list:
        pdf_files = sorted(glob.glob(f"{folder}/*.pdf"))
        results = []
        for pdf_path in pdf_files:
            print(f"Processing {Path(pdf_path).name}...", end=" ")
            result = self.process_resume(pdf_path)
            if result["success"]:
                print(
                    f"OK  ({result['extraction_time']:.2f}s, "
                    f"ATS: {result['ats_score']}, "
                    f"NER fields: {result['ner_field_count']}, "
                    f"LLM fields: {result['llm_field_count']})"
                )
            else:
                print(f"FAILED  ({result['error']})")
            results.append(result)
        return results


if __name__ == "__main__":
    pipeline = ResumeParsingPipeline()
    results = pipeline.process_batch("data/raw")

    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]

    print("\n=== SUMMARY ===")
    print(f"Total files: {len(results)}")
    print(f"Succeeded: {len(successes)}")
    print(f"Failed: {len(failures)}")

    if successes:
        avg_time = sum(r["extraction_time"] for r in successes) / len(successes)
        scored = [r["ats_score"] for r in successes if r["ats_score"] is not None]
        avg_score = sum(scored) / len(scored) if scored else None
        llm_hits = sum(1 for r in successes if r["llm_field_count"] > 0)
        print(f"Avg extraction time: {avg_time:.2f}s")
        if avg_score is not None:
            print(f"Avg ATS score: {avg_score:.1f}")
        print(f"Resumes with LLM data (Gemini succeeded): {llm_hits}/{len(successes)}")

    if failures:
        print("\nFailed files:")
        for r in failures:
            print(f"  - {r['file']}: {r['error']}")

    Path("results").mkdir(exist_ok=True)
    with open("results/batch_inference_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nFull results saved to results/batch_inference_results.json (now hybrid — see hybrid_fields per entry)")
