"""Prints one ✅/❌ line per eval case from the newest agents-cli results file.

Usage: uv run python evals/summary.py [results_dir]   (default: artifacts/eval_results)
"""

import json
import sys
from pathlib import Path

results_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts/eval_results")
results = json.loads(sorted(results_dir.glob("results_*.json"))[-1].read_text())
cases = results["evaluation_dataset"][0]["eval_cases"]

passed = 0
for case, result in zip(cases, results["eval_case_results"], strict=True):
    check = result["response_candidate_results"][0]["metric_results"]["checks"]
    ok = check["score"] == 1.0
    passed += ok
    reason = "" if ok else f"   ← {check['explanation'] or check['error_message']}"
    print(f"  {'✅' if ok else '❌'}  {case['eval_case_id']}{reason[:160]}")

print(f"\n  {passed}/{len(cases)} passed")
sys.exit(0 if passed == len(cases) else 1)
