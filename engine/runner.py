import asyncio
import time
from typing import List, Dict, Tuple
from tqdm.asyncio import tqdm
# Import other components...


class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge
        self.semaphore = asyncio.Semaphore(5)

    async def run_single_test(self, test_case: Dict, pbar: tqdm) -> Dict:
        async with self.semaphore:
            start_time = time.perf_counter()

            # 1. Gọi Agent
            response = await self.agent.query(test_case["question"])
            latency = time.perf_counter() - start_time

            # 2. Chạy RAGAS metrics
            ragas_scores = await self.evaluator.score(test_case, response)

            # 3. Chạy Multi-Judge
            judge_result = await self.judge.evaluate_multi_judge(
                test_case["question"],
                response["answer"],
                test_case["expected_answer"]
            )

            # Extract cost if available (handle dict or object)
            agent_cost = response.get("metadata", {}).get("cost_usd", 0.0) if isinstance(
                response, dict) else getattr(response, "cost_usd", 0.0)
            judge_cost = judge_result.get("cost_usd", 0.0) if isinstance(
                judge_result, dict) else getattr(judge_result, "cost_usd", 0.0)

            pbar.update(1)

            return {
                "test_case": test_case["question"],
                "agent_response": response["answer"] if isinstance(response, dict) else getattr(response, "answer", response),
                "latency": latency,
                "ragas": ragas_scores,
                "judge": judge_result,
                "status": "fail" if judge_result.get("final_score", 0) < 3 else "pass",
                "cost_usd": agent_cost + judge_cost
            }

    async def run_all(self, dataset: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        Chạy song song bằng asyncio.gather với Semaphore để giới hạn concurrent calls.
        """
        start_time = time.perf_counter()

        with tqdm(total=len(dataset), desc="Running benchmark") as pbar:
            tasks = [self.run_single_test(case, pbar) for case in dataset]
            results = await asyncio.gather(*tasks)

        total_time = time.perf_counter() - start_time
        total_cost = sum(r.get("cost_usd", 0.0) for r in results)
        avg_latency = sum(r.get("latency", 0.0)
                          for r in results) / len(results) if results else 0.0

        performance = {
            "total_time_seconds": round(total_time, 2),
            "avg_latency_per_case": round(avg_latency, 2),
            "total_cost_usd": round(total_cost, 4),
            "cost_per_case_usd": round(total_cost / len(results), 4) if results else 0.0
        }

        return results, performance
