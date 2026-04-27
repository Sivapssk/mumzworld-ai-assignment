import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from app import process_input


def load_cases(path: Path) -> List[Dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_cases(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    passed = 0

    for idx, case in enumerate(cases, start=1):
        output_json, note = process_input(case["input"])

        parsed = {}
        parse_error = None
        try:
            parsed = json.loads(output_json)
        except Exception as exc:
            parse_error = str(exc)

        actual = parsed.get("intent")
        expected = case.get("expected")
        is_pass = actual == expected and parse_error is None
        if is_pass:
            passed += 1

        rows.append(
            {
                "case_id": idx,
                "input": case["input"],
                "expected_intent": expected,
                "actual_intent": actual,
                "pass": is_pass,
                "needs_human": parsed.get("needs_human"),
                "confidence": parsed.get("confidence"),
                "error": parsed.get("error") or parse_error,
                "escalation_note": note,
                "raw_output": parsed if parsed else output_json,
            }
        )

    total = len(cases)
    accuracy = round((passed / total) * 100, 2) if total else 0.0
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_cases": total,
        "passed_cases": passed,
        "accuracy_percent": accuracy,
        "results": rows,
    }


def write_json_report(report: Dict[str, Any], out_path: Path) -> None:
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def write_markdown_report(report: Dict[str, Any], out_path: Path) -> None:
    lines = [
        "# Evaluation Proof Report",
        "",
        f"- Generated (UTC): `{report['generated_at_utc']}`",
        f"- Total Cases: `{report['total_cases']}`",
        f"- Passed Cases: `{report['passed_cases']}`",
        f"- Accuracy: `{report['accuracy_percent']}%`",
        "",
        "## Case-by-case Results",
        "",
        "| # | Input | Expected | Actual | Pass | Needs Human | Confidence | Error |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in report["results"]:
        input_text = str(row["input"]).replace("|", "\\|")
        expected = row["expected_intent"]
        actual = row["actual_intent"]
        passed = "✅" if row["pass"] else "❌"
        needs_human = row["needs_human"]
        confidence = row["confidence"]
        error = row["error"] if row["error"] else "-"
        error = str(error).replace("|", "\\|")
        lines.append(
            f"| {row['case_id']} | {input_text} | {expected} | {actual} | {passed} | {needs_human} | {confidence} | {error} |"
        )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    cases_path = Path("test_cases.json")
    json_out = Path("EVAL_RESULTS.json")
    md_out = Path("EVAL_RESULTS.md")

    report = run_cases(load_cases(cases_path))
    write_json_report(report, json_out)
    write_markdown_report(report, md_out)

    print(f"Saved: {json_out}")
    print(f"Saved: {md_out}")
    print(
        f"Summary: {report['passed_cases']}/{report['total_cases']} "
        f"({report['accuracy_percent']}%)"
    )


if __name__ == "__main__":
    main()
