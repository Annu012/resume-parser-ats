"""Resume Processing Pipeline — batch mode over data/raw/"""
import time
import glob
import json
from pathlib import Path
from src.resume_parser import ResumeParser
from src.ats_scorer import ATSScorer


class ResumeParsingPipeline:
    def __init__(self):
        self.parser = ResumeParser()
        self.scorer = ATSScorer()

    def process_resume(self, pdf_path: str) -> dict:
        start = time.time()
        try:
            text = self.parser.extract_text_from_pdf(pdf_path)
            entities = self.parser.extract_entities(text)
            ats_result = self.scorer.calculate_score(text)

            return {
                "file": Path(pdf_path).name,
                "extraction_time": time.time() - start,
                "entity_types_found": len(entities),
                "entities_total": sum(len(v) for v in entities.values()),
                "ats_score": ats_result["total_score"],
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "file": Path(pdf_path).name,
                "extraction_time": time.time() - start,
                "entity_types_found": 0,
                "entities_total": 0,
                "ats_score": None,
                "success": False,
                "error": str(e)
            }

    def process_batch(self, folder: str = "data/raw") -> list:
        pdf_files = sorted(glob.glob(f"{folder}/*.pdf"))
        results = []
        for pdf_path in pdf_files:
            print(f"Processing {Path(pdf_path).name}...", end=" ")
            result = self.process_resume(pdf_path)
            if result["success"]:
                print(f"OK  ({result['extraction_time']:.2f}s, ATS: {result['ats_score']:.1f}, entities: {result['entities_total']})")
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
        avg_score = sum(r["ats_score"] for r in successes) / len(successes)
        print(f"Avg extraction time: {avg_time:.2f}s")
        print(f"Avg ATS score: {avg_score:.1f}")

    if failures:
        print("\nFailed files:")
        for r in failures:
            print(f"  - {r['file']}: {r['error']}")

    Path("results").mkdir(exist_ok=True)
    with open("results/batch_inference_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nFull results saved to results/batch_inference_results.json")