import os
import json
import asyncio
import random
from typing import Dict, Any

# Lightweight implementation that attempts to call OpenAI (gpt-4o) and Google Gemini (gemini-3.1-pro-preview).
# If SDKs are not available at runtime, falls back to a deterministic mock to keep behavior predictable.

try:
    import openai
    from openai import AsyncOpenAI, RateLimitError as OpenAIRateLimitError
except Exception:
    openai = None
    AsyncOpenAI = None
    OpenAIRateLimitError = Exception

try:
    import google.generativeai as genai
except Exception:
    genai = None


class LLMJudge:
    def __init__(self, gpt_model: str = "gpt-4o", gemini_model: str = "gemini-3.1-pro-preview", verbosity: str = "high"):
        self.gpt_model = gpt_model
        self.gemini_model = gemini_model
        self.verbosity = verbosity
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

        # Modern AsyncOpenAI client (openai >= 1.0)
        self._openai_client = None
        if AsyncOpenAI and self.openai_key:
            self._openai_client = AsyncOpenAI(api_key=self.openai_key)

        if genai and self.gemini_key:
            genai.configure(api_key=self.gemini_key)

        # Models that do NOT support temperature parameter
        self._no_temperature_models = {"o1", "o1-mini", "o3", "o3-mini", "o4-mini"}

        # Rubric for evaluating the answers based on multiple criteria
        self.rubric_prompt = (
            "Evaluate the provided ANSWER against the GROUND_TRUTH based on three criteria:\n"
            "1. Accuracy: Does it correctly address the question using only the ground truth?\n"
            "2. Professionalism: Is the tone professional and appropriate?\n"
            "3. Hallucination-free: Does it avoid making up facts not present in the ground truth?\n\n"
            "Score on a 1-5 scale (1 worst, 5 best). Return JSON: {\"score\": float, \"reasoning\": \"str\"}. Be concise."
        )

    async def _call_gpt(self, question: str, answer: str, ground_truth: str, max_retries: int = 4) -> Dict[str, Any]:
        prompt = (
            f"{self.rubric_prompt}\nQUESTION: {question}\nANSWER: {answer}\nGROUND_TRUTH: {ground_truth}\nRespond only with valid JSON."
        )

        if not self._openai_client:
            print(f"   ❌ [LLMJudge] OpenAI client chưa được khởi tạo (thiếu OPENAI_API_KEY?) — dùng MOCK SCORE")
            return _mock_score(answer, ground_truth, provider="gpt-mock")

        # Kiểm tra model có hỗ trợ temperature không
        supports_temp = not any(m in self.gpt_model.lower() for m in self._no_temperature_models)
        create_kwargs = dict(
            model=self.gpt_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
        )
        if supports_temp:
            create_kwargs["temperature"] = 0

        last_err = None
        for attempt in range(max_retries):
            try:
                resp = await self._openai_client.chat.completions.create(**create_kwargs)
                content = resp.choices[0].message.content
                p_tokens = resp.usage.prompt_tokens if resp.usage else 0
                c_tokens = resp.usage.completion_tokens if resp.usage else 0
                parsed = _parse_json_like(content)
                parsed.setdefault("tokens", p_tokens + c_tokens)
                parsed.setdefault("cost_usd", _estimate_cost(self.gpt_model, p_tokens, c_tokens))
                return parsed
            except OpenAIRateLimitError as e:
                last_err = e
                wait = min(60, (2 ** attempt) + random.uniform(0, 1))
                print(f"   ⚠️  [LLMJudge] GPT rate limit (attempt {attempt+1}/{max_retries}), chờ {wait:.1f}s...")
                await asyncio.sleep(wait)
            except Exception as e:
                print(f"   ⚠️  [LLMJudge] GPT ({self.gpt_model}) thất bại: {type(e).__name__}: {e}")
                break

        # Tất cả attempts đều thất bại → dùng mock
        print(f"   ❌ [LLMJudge] Không thể gọi GPT ({self.gpt_model}) — dùng MOCK SCORE (kết quả không đáng tin cậy!)")
        return _mock_score(answer, ground_truth, provider="gpt-mock")

    async def _call_gemini(self, question: str, answer: str, ground_truth: str, model_override: str = None) -> Dict[str, Any]:
        model = model_override or self.gemini_model
        prompt = (
            f"{self.rubric_prompt}\nQUESTION: {question}\nANSWER: {answer}\nGROUND_TRUTH: {ground_truth}\nRespond only with valid JSON."
        )

        # Try Google Generative AI client if available
        if genai and hasattr(genai, "chat"):
            try:
                # genai.chat.create is synchronous in many SDKs; wrap in thread
                resp = await asyncio.to_thread(lambda: genai.chat.create(model=model, messages=[{"content": prompt, "author": "user"}]))
                # SDKs differ in shape; attempt common accesses
                content = getattr(resp, "content", None) or (resp.get("candidates")[0].get("content") if resp.get("candidates") else None)
                if not content and isinstance(resp, dict):
                    content = resp.get("candidates", [{}])[0].get("content")
                parsed = _parse_json_like(content or "")

                # Try to extract usage from genai response
                usage = getattr(resp, "usage_metadata", None)
                p_tokens = getattr(usage, "prompt_token_count", 0)
                c_tokens = getattr(usage, "candidates_token_count", 0)

                if not p_tokens and isinstance(resp, dict):
                    u = resp.get("usage", {})
                    p_tokens = u.get("prompt_tokens", u.get("prompt_token_count", 0))
                    c_tokens = u.get("completion_tokens", u.get("candidates_token_count", 0))

                parsed.setdefault("tokens", p_tokens + c_tokens)
                parsed.setdefault("cost_usd", _estimate_cost(model, p_tokens, c_tokens))
                parsed["_model_used"] = model
                return parsed
            except Exception as e:
                print(f"   ⚠️  [LLMJudge] Gemini ({model}) thất bại: {type(e).__name__}: {e}")

        # Fallback sang gemini-2.5-pro nếu primary model thất bại
        _FALLBACK_GEMINI = "gemini-2.5-pro"
        if model != _FALLBACK_GEMINI:
            print(f"   🔄 [LLMJudge] Thử fallback sang {_FALLBACK_GEMINI}...")
            return await self._call_gemini(question, answer, ground_truth, model_override=_FALLBACK_GEMINI)

        # Tất cả Gemini paths đều thất bại → dùng mock
        print(f"   ❌ [LLMJudge] Không thể gọi Gemini ({model}) — dùng MOCK SCORE (kết quả không đáng tin cậy!)")
        return _mock_score(answer, ground_truth, provider="gemini-mock")

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """Call both judges concurrently, compute aggregated score, agreement and handle large disagreements.
        Returns a dict with final_score, agreement_rate, individual_scores, reasonings, tokens_used, cost_usd, conflict_resolved.
        """
        a_task = asyncio.create_task(self._call_gpt(question, answer, ground_truth))
        b_task = asyncio.create_task(self._call_gemini(question, answer, ground_truth))
        a_res, b_res = await asyncio.gather(a_task, b_task)

        score_a = float(a_res.get("score", 0))
        score_b = float(b_res.get("score", 0))
        avg_score = (score_a + score_b) / 2.0

        # Calculate agreement rate using Quadratic Weighted Kappa approximation for a single instance
        # Formula: 1 - ((score_a - score_b)^2 / (max_score - min_score)^2)
        # Here max_score = 5, min_score = 1, so denominator is 16.0
        agreement_rate = max(0.0, 1.0 - ((score_a - score_b) ** 2) / 16.0)

        conflict_resolved = False
        tie_break_reasoning = None

        # If models disagree by >1 point, call the GPT judge (gpt model) as tie-breaker
        if abs(score_a - score_b) > 1.0:
            tb = await self._call_gpt(question + "\n(Tie-breaker request)", answer, ground_truth)
            tb_score = float(tb.get("score", avg_score))
            avg_score = tb_score
            conflict_resolved = True
            tie_break_reasoning = tb.get("reasoning")

        total_tokens = _sum_optional(a_res.get("tokens"), b_res.get("tokens"))
        total_cost = _sum_optional(a_res.get("cost_usd"), b_res.get("cost_usd"))

        return {
            "final_score": avg_score,
            "agreement_rate": agreement_rate,
            "individual_scores": {self.gpt_model: score_a, self.gemini_model: score_b},
            "reasoning": {self.gpt_model: a_res.get("reasoning"), self.gemini_model: b_res.get("reasoning")},
            "conflict_resolved": conflict_resolved,
            "tie_break_reasoning": tie_break_reasoning,
            "tokens_used": total_tokens,
            "cost_usd": total_cost,
        }

    async def check_position_bias(self, question: str, response_a: str, response_b: str, ground_truth: str) -> Dict[str, Any]:
        """Check position bias by asking judges to compare two responses in order A vs B and then B vs A.
        If aggregated decisions change, flag position bias.
        Returns a dict with has_position_bias and detailed results.
        """
        compare_prompt = (
            "Given QUESTION and GROUND_TRUTH, compare RESPONSE_A and RESPONSE_B and return JSON {\"winner\": \"A|B|tie\", \"reasoning\": str}."
        )

        # Build combined answers for comparison
        ans_ab = f"RESPONSE_A: {response_a}\nRESPONSE_B: {response_b}"
        ans_ba = f"RESPONSE_A: {response_b}\nRESPONSE_B: {response_a}"

        # Ask GPT and Gemini for both orders
        tasks = [
            asyncio.create_task(self._call_gpt(question + "\nCOMPARE", ans_ab, ground_truth)),
            asyncio.create_task(self._call_gemini(question + "\nCOMPARE", ans_ab, ground_truth)),
            asyncio.create_task(self._call_gpt(question + "\nCOMPARE_REVERSED", ans_ba, ground_truth)),
            asyncio.create_task(self._call_gemini(question + "\nCOMPARE_REVERSED", ans_ba, ground_truth)),
        ]
        r1, r2, r3, r4 = await asyncio.gather(*tasks)

        winners_first = [r1.get("winner"), r2.get("winner")]
        winners_second = [r3.get("winner"), r4.get("winner")]

        # If any winner changes across orders, flag position bias
        has_bias = winners_first != winners_second

        return {
            "position_bias_detected": bool(has_bias),
            "first_order": {self.gpt_model: r1, self.gemini_model: r2},
            "second_order": {self.gpt_model: r3, self.gemini_model: r4},
        }


# --- Helper utilities ---

def _parse_json_like(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    # Try direct JSON
    try:
        return json.loads(text)
    except Exception:
        pass
    # Try to find a JSON substring
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass
    # Fallback: heuristic extraction
    score = None
    reasoning = text
    for token in ["score", "rating", "points"]:
        if token in text.lower():
            import re

            m = re.search(r"(\d(?:\.\d)?)", text)
            if m:
                score = float(m.group(1))
                break
    return {"score": score if score is not None else 3, "reasoning": reasoning}


def _estimate_cost(model: str, prompt_tokens: Any = 0, completion_tokens: Any = 0) -> float:
    # Market cost rates per 1k tokens (Input vs Output)
    p = float(prompt_tokens or 0)
    c = float(completion_tokens or 0)

    if "gpt-5" in model.lower():
        # GPT-5 Medium: Input $0.00125, Output $0.01000
        in_rate = 0.00125
        out_rate = 0.01000
        return round((p / 1000.0) * in_rate + (c / 1000.0) * out_rate, 6)

    if "gemini-3.1-pro-preview" in model.lower():
        # Gemini 3.1 Pro Preview: Price depends on prompt length
        if p <= 200000:
            in_rate = 0.0020
            out_rate = 0.0120
        else:
            in_rate = 0.0040
            out_rate = 0.0180
        return round((p / 1000.0) * in_rate + (c / 1000.0) * out_rate, 6)

    if "gemini-2.5-pro" in model.lower():
        # Gemini 2.5 Pro: Input $1.25/1M (≤200k), Output $10.00/1M (≤200k tokens)
        # Long-context (>200k): Input $2.50/1M, Output $15.00/1M
        if p <= 200000:
            in_rate = 0.00125
            out_rate = 0.01000
        else:
            in_rate = 0.00250
            out_rate = 0.01500
        return round((p / 1000.0) * in_rate + (c / 1000.0) * out_rate, 6)

    # Fallback rates for other models (e.g. gpt-4o, gpt-4o-mini)
    rates = {
        "gpt-4o": {"in": 0.005, "out": 0.015},
        "gpt-4o-mini": {"in": 0.00015, "out": 0.0006},
        "gemini-3.1-pro": {"in": 0.00125, "out": 0.00375},
        "gemini": {"in": 0.000125, "out": 0.000375},
    }
    r = rates.get(model.lower(), {"in": 0.002, "out": 0.006})
    return round((p / 1000.0) * r["in"] + (c / 1000.0) * r["out"], 6)


def _sum_optional(a, b):
    try:
        return (float(a) if a is not None else 0.0) + (float(b) if b is not None else 0.0)
    except Exception:
        return None


def _mock_score(answer: str, ground_truth: str, provider: str = "mock") -> Dict[str, Any]:
    # Deterministic mock: score=5 if answer contains word from ground_truth, else 3.
    score = 3
    for w in (ground_truth or "").split():
        if w and w.lower() in (answer or "").lower():
            score = 5
            break
    return {"score": score, "reasoning": f"Mocked by {provider}", "tokens": 10, "cost_usd": 0.0}
