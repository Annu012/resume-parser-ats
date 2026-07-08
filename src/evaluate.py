

import csv
import json
from pathlib import Path

GROUND_TRUTH_PATH = Path("ground_truth.csv")
PARSED_OUTPUT_PATH = Path("results/parsed_output.json")
REPORT_PATH = Path("results/evaluation_report.json")

FIELDS = ["name", "email", "phone", "experience_years", "education", "skills"]


def load_ground_truth(path: Path) -> dict[str, dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Copy ground_truth_template.csv to "
            f"ground_truth.csv and fill in the true_* columns by hand first."
        )
    truth = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filled = [row[f"true_{field}"] for field in FIELDS if row.get(f"true_{field}", "").strip()]
            if not filled:
                continue  # skip rows that haven't been labeled yet
            truth[row["file"]] = {field: row[f"true_{field}"].strip() for field in FIELDS}
    if not truth:
        raise ValueError(
            "ground_truth.csv exists but no rows have been filled in yet. "
            "Label at least a few resumes before running evaluation."
        )
    return truth


def load_parsed_output(path: Path) -> dict[str, dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run your parser on the labeled resumes and "
            f"save output in the expected format first (see script docstring)."
        )
    with open(path) as f:
        records = json.load(f)
    return {r["file"]: r for r in records}


def _normalize(value) -> str:
    if isinstance(value, list):
        return ",".join(sorted(str(v).strip().lower() for v in value))
    return str(value).strip().lower()


def evaluate(truth: dict[str, dict], predicted: dict[str, dict]) -> dict:
    field_correct = {f: 0 for f in FIELDS}
    field_total = {f: 0 for f in FIELDS}
    per_file_results = []
    skipped_files = []

    for file, true_fields in truth.items():
        if file not in predicted:
            skipped_files.append(file)
            continue

        pred_fields = predicted[file]
        file_result = {"file": file, "fields": {}}

        for field in FIELDS:
            true_val = true_fields.get(field, "")
            if not true_val:
                continue  # this field wasn't labeled for this resume
            pred_val = pred_fields.get(field, "")

            correct = _normalize(true_val) == _normalize(pred_val)
            field_total[field] += 1
            if correct:
                field_correct[field] += 1

            file_result["fields"][field] = {
                "true": true_val, "predicted": pred_val, "correct": correct
            }
        per_file_results.append(file_result)

    per_field_accuracy = {
        f: round(field_correct[f] / field_total[f], 4) if field_total[f] else None
        for f in FIELDS
    }
    total_correct = sum(field_correct.values())
    total_labeled = sum(field_total.values())
    overall_accuracy = round(total_correct / total_labeled, 4) if total_labeled else None

    return {
        "num_resumes_evaluated": len(per_file_results),
        "num_resumes_skipped_no_prediction": len(skipped_files),
        "skipped_files": skipped_files,
        "per_field_accuracy": per_field_accuracy,
        "overall_accuracy": overall_accuracy,
        "per_file_results": per_file_results,
    }


def main():
    truth = load_ground_truth(GROUND_TRUTH_PATH)
    predicted = load_parsed_output(PARSED_OUTPUT_PATH)

    report = evaluate(truth, predicted)

    print(f"Evaluated {report['num_resumes_evaluated']} resumes")
    if report["num_resumes_skipped_no_prediction"]:
        print(f"WARNING: {report['num_resumes_skipped_no_prediction']} labeled "
              f"resumes had no matching prediction: {report['skipped_files']}")
    print("\nPer-field accuracy:")
    for field, acc in report["per_field_accuracy"].items():
        print(f"  {field:20s} {acc if acc is not None else 'N/A (no labels)'}")
    print(f"\nOverall accuracy: {report['overall_accuracy']}")

    REPORT_PATH.parent.mkdir(exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved full report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
