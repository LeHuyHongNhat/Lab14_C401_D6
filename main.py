import asyncio
import json
import os
import time
from engine.runner import BenchmarkRunner
from engine.llm_judge import LLMJudge
from agent.main_agent import MainAgent


# ─────────────────────────────────────────────────────────────────────────────
# ExpertEvaluator: tính Hit Rate và MRR thực từ retrieved_ids
# ─────────────────────────────────────────────────────────────────────────────
class ExpertEvaluator:
    async def score(self, case: dict, resp: dict) -> dict:
        expected = case.get("expected_retrieval_ids", [])
        retrieved = resp.get("retrieved_ids", [])

        # Hit Rate: có ít nhất 1 expected ID trong top-3 retrieved không?
        top_k = retrieved[:3]
        hit_rate = 1.0 if any(eid in top_k for eid in expected) else 0.0

        # MRR: 1 / vị trí đầu tiên của expected_id trong retrieved (1-indexed)
        mrr = 0.0
        for i, doc_id in enumerate(retrieved):
            if doc_id in expected:
                mrr = 1.0 / (i + 1)
                break

        return {
            "faithfulness": 0.9,
            "relevancy": 0.85,
            "retrieval": {"hit_rate": hit_rate, "mrr": mrr},
        }


# ─────────────────────────────────────────────────────────────────────────────
# MultiModelJudge: wrapper dùng LLMJudge thật (GPT-5 + Gemini)
# ─────────────────────────────────────────────────────────────────────────────
class MultiModelJudge:
    def __init__(self):
        self._judge = LLMJudge()

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> dict:
        return await self._judge.evaluate_multi_judge(question, answer, ground_truth)


# ─────────────────────────────────────────────────────────────────────────────
# Release Gate — multi-criteria
# ─────────────────────────────────────────────────────────────────────────────
def _release_gate(v1: dict, v2: dict) -> dict:
    """
    APPROVE : score_delta >= 0  AND  cost_delta <= 0.1  AND  hit_rate_delta >= -0.05
    BLOCK   : score_delta < -0.2  OR  hit_rate_delta < -0.1
    WARN    : mọi trường hợp còn lại
    """
    m1, m2 = v1.get("metrics", {}), v2.get("metrics", {})

    score_delta    = m2.get("avg_score", 0)   - m1.get("avg_score", 0)
    hit_rate_delta = m2.get("hit_rate", 0)    - m1.get("hit_rate", 0)
    mrr_delta      = m2.get("mrr", 0)         - m1.get("mrr", 0)
    cost_delta     = m2.get("total_cost_usd", 0) - m1.get("total_cost_usd", 0)
    latency_delta  = (m2.get("performance", {}).get("avg_latency_per_case", 0)
                    - m1.get("performance", {}).get("avg_latency_per_case", 0))

    reasons = []
    if score_delta >= 0:
        reasons.append(f"Score tăng {score_delta:+.3f}")
    else:
        reasons.append(f"Score giảm {score_delta:.3f}")

    if hit_rate_delta >= 0:
        reasons.append(f"Hit Rate tăng {hit_rate_delta:+.3f}")
    else:
        reasons.append(f"Hit Rate giảm {hit_rate_delta:.3f}")

    if cost_delta <= 0:
        reasons.append(f"Cost giảm {abs(cost_delta):.6f} USD")
    else:
        reasons.append(f"Cost tăng {cost_delta:.6f} USD")

    # Decision logic
    if score_delta < -0.2 or hit_rate_delta < -0.1:
        decision = "BLOCK"
    elif score_delta >= 0 and cost_delta <= 0.1 and hit_rate_delta >= -0.05:
        decision = "APPROVE"
    else:
        decision = "WARN"

    return {
        "score_delta":     round(score_delta, 4),
        "hit_rate_delta":  round(hit_rate_delta, 4),
        "mrr_delta":       round(mrr_delta, 4),
        "cost_delta":      round(cost_delta, 6),
        "latency_delta":   round(latency_delta, 4),
        "decision":        decision,
        "reasons":         reasons,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Chạy benchmark cho 1 phiên bản agent
# ─────────────────────────────────────────────────────────────────────────────
async def run_benchmark(agent_version: str, agent_v: str = "v1") -> tuple:
    print(f"\n🚀 Khởi động Benchmark cho {agent_version} (agent {agent_v.upper()})...")

    if not os.path.exists("data/golden_set.jsonl"):
        print("❌ Thiếu data/golden_set.jsonl. Chạy 'python data/synthetic_gen.py' trước.")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("❌ File data/golden_set.jsonl rỗng.")
        return None, None

    agent    = MainAgent(version=agent_v)
    evaluator = ExpertEvaluator()
    judge    = MultiModelJudge()
    runner   = BenchmarkRunner(agent, evaluator, judge)

    results, performance = await runner.run_all(dataset)
    total = len(results)

    avg_score       = sum(r["judge"].get("final_score", 0)           for r in results) / total if total else 0.0
    avg_hit_rate    = sum(r["ragas"]["retrieval"].get("hit_rate", 0) for r in results) / total if total else 0.0
    avg_mrr         = sum(r["ragas"]["retrieval"].get("mrr", 0)      for r in results) / total if total else 0.0
    avg_agreement   = sum(r["judge"].get("agreement_rate", 0)        for r in results) / total if total else 0.0

    summary = {
        "metadata": {
            "version":   agent_version,
            "total":     total,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "metrics": {
            "avg_score":       round(avg_score, 4),
            "hit_rate":        round(avg_hit_rate, 4),
            "mrr":             round(avg_mrr, 4),
            "agreement_rate":  round(avg_agreement, 4),
            "total_cost_usd":  round(performance.get("total_cost_usd", 0), 6),
        },
        "performance": performance,
    }
    return results, summary


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
async def main():
    v1_results, v1_summary = await run_benchmark("Agent_V1_Base", agent_v="v1")
    v2_results, v2_summary = await run_benchmark("Agent_V2_Optimized", agent_v="v2")

    if not v1_summary or not v2_summary:
        print("❌ Benchmark thất bại — kiểm tra data/golden_set.jsonl.")
        return

    # ── Regression Gate ────────────────────────────────────────────────────
    gate = _release_gate(v1_summary, v2_summary)

    print("\n📊 ── KẾT QUẢ REGRESSION ──────────────────────────────────────")
    print(f"   V1 avg_score  : {v1_summary['metrics']['avg_score']:.4f}")
    print(f"   V2 avg_score  : {v2_summary['metrics']['avg_score']:.4f}")
    print(f"   Score delta   : {gate['score_delta']:+.4f}")
    print(f"   Hit Rate delta: {gate['hit_rate_delta']:+.4f}")
    print(f"   Cost delta    : {gate['cost_delta']:+.6f} USD")
    print(f"   Reasons       : {' | '.join(gate['reasons'])}")
    print(f"\n   ➡  Quyết định: {gate['decision']}")

    if gate["decision"] == "APPROVE":
        print("✅ CHẤP NHẬN BẢN CẬP NHẬT (APPROVE)")
    elif gate["decision"] == "WARN":
        print("⚠️  CẢNH BÁO — Xem xét thủ công trước khi deploy (WARN)")
    else:
        print("❌ TỪ CHỐI (BLOCK RELEASE)")

    # ── Ghi reports ────────────────────────────────────────────────────────
    os.makedirs("reports", exist_ok=True)

    # Gắn thêm regression vào summary của V2
    v2_summary["metadata"]["regression"] = {
        "v1_score":   v1_summary["metrics"]["avg_score"],
        "v2_score":   v2_summary["metrics"]["avg_score"],
        "decision":   gate["decision"],
    }

    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)

    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    regression_report = {
        "v1_summary": v1_summary,
        "v2_summary": v2_summary,
        "gate":       gate,
        "timestamp":  time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open("reports/regression_report.json", "w", encoding="utf-8") as f:
        json.dump(regression_report, f, ensure_ascii=False, indent=2)

    print("\n📁 Đã ghi:")
    print("   reports/summary.json")
    print("   reports/benchmark_results.json")
    print("   reports/regression_report.json")


if __name__ == "__main__":
    asyncio.run(main())
