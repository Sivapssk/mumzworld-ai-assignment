# Evaluation

## Evaluation Rubric
A test case is PASS if:
- Intent is correct
- JSON is valid
- Arabic is natural
- Out-of-scope is rejected

## Results

| Input | Expected | Actual | Pass | Notes |
|------|--------|--------|------|------|
| damaged stroller | refund | refund | ✅ | correct |
| weather query | null | null | ✅ | good refusal |
| vague complaint | escalate | refund | ❌ | overconfidence |

## Metrics
- Accuracy: 83%
- JSON Validity: 100%
- Refusal Handling: 100%

## Failure Mode
- Overconfidence in vague inputs
