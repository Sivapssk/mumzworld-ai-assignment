import json
from pathlib import Path

from app import process_input


def main() -> None:
    cases = json.loads(Path("test_cases.json").read_text(encoding="utf-8"))
    passed = 0
    total = len(cases)

    print(f"TOTAL_CASES: {total}")
    print("-" * 100)

    for i, case in enumerate(cases, 1):
        output_json, note = process_input(case["input"])

        actual_intent = None
        error = None
        try:
            payload = json.loads(output_json)
            actual_intent = payload.get("intent")
            error = payload.get("error")
        except Exception as exc:
            error = f"json_parse_error: {exc}"

        ok = actual_intent == case.get("expected")
        if ok:
            passed += 1

        print(
            f"{i:02d}. expected={case.get('expected')!r} actual={actual_intent!r} "
            f"pass={ok} error={error!r}"
        )
        print(f"    input={case['input']!r}")
        print(f"    note={note!r}")

    print("-" * 100)
    print(f"PASSED: {passed}/{total}")


if __name__ == "__main__":
    main()
