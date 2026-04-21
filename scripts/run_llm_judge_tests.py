#!/usr/bin/env python3
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure project root is importable when script runs directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from engine.llm_judge import LLMJudge
except Exception as e:
    print("ERROR_IMPORTING_LLMJUDGE", e)
    raise

INPUT = "data/golden_set.jsonl"
OUT = "reports/llm_judge_results.json"

if not os.path.exists(INPUT):
    print("MISSING_GOLDEN_SET")
    sys.exit(2)

async def run_all():
    with open(INPUT, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]

    judge = LLMJudge()
    sem = asyncio.Semaphore(5)

    async def worker(case: Any):
        q = case.get("question", "")
        gt = case.get("expected_answer") or case.get("ground_truth") or ""
        ans = case.get("model_answer", gt)
        async with sem:
            return await judge.evaluate_multi_judge(q, ans, gt)

    tasks = [worker(c) for c in lines]
    results = await asyncio.gather(*tasks)

    per_case = []
    total_tokens = 0.0
    total_cost = 0.0
    total_score = 0.0
    total_agreement = 0.0

    for case, res in zip(lines, results):
        per_case.append({
            "question": case.get("question"),
            "final_score": res.get("final_score"),
            "agreement_rate": res.get("agreement_rate"),
            "tokens_used": res.get("tokens_used"),
            "cost_usd": res.get("cost_usd"),
        })
        try:
            total_score += float(res.get("final_score") or 0)
        except Exception:
            pass
        try:
            total_agreement += float(res.get("agreement_rate") or 0)
        except Exception:
            pass
        try:
            total_tokens += float(res.get("tokens_used") or 0)
        except Exception:
            pass
        try:
            total_cost += float(res.get("cost_usd") or 0)
        except Exception:
            pass

    n = len(results)
    summary = {
        "avg_final_score": (total_score / n) if n else 0,
        "avg_agreement": (total_agreement / n) if n else 0,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "cases": n,
    }

    out = {"summary": summary, "per_case": per_case}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False))
    print("WROTE", OUT)

if __name__ == "__main__":
    asyncio.run(run_all())
