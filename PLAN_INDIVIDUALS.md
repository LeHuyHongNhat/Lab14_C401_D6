# 🏆 KẾ HOẠCH CHI TIẾT - Lab Day 14: AI Evaluation Factory
> **Mục tiêu:** 100/100 điểm | **Nhóm:** 6 thành viên C401-D6 | **Thời gian:** 4 giờ

---

## 👥 Phân công vai trò & Tổng quan phụ thuộc

```
[GIAI ĐOẠN 1 - Song song] ──────────────────────────────────────────────────
  Khánh   → data/synthetic_gen.py        (SDG - tạo 50+ golden dataset)
  Khải    → agent/main_agent.py          (Upgrade RAG Agent thực)

[GIAI ĐOẠN 2 - Phụ thuộc vào GĐ1] ─────────────────────────────────────────
  Nhật    → engine/llm_judge.py          (Multi-Judge: GPT + Claude)
  Tấn     → engine/retrieval_eval.py
            engine/runner.py             (Async Runner + Cost tracking)

  ⚠️  Nhật & Tấn chờ golden_set.jsonl FILE LOCK → Khánh xong thì unlock

[GIAI ĐOẠN 3 - Phụ thuộc vào GĐ2] ─────────────────────────────────────────
  Thành   → main.py (Regression Release Gate)
  Sơn     → analysis/failure_analysis.md (5 Whys deep-dive)

  ⚠️  Thành chờ runner.py ổn định (Tấn xong)
  ⚠️  Sơn chờ benchmark chạy xong, có kết quả thực

[GIAI ĐOẠN 4 - Tất cả] ─────────────────────────────────────────────────────
  Mọi người → Viết reflection cá nhân + Review lần cuối
```

---

## 📊 Bảng điểm mục tiêu

| Hạng mục | Điểm | Người phụ trách |
|---|:---:|---|
| **[Nhóm] Retrieval Eval** (Hit Rate + MRR ≥ 50 cases) | 10 | Tấn chính, Khánh hỗ trợ data |
| **[Nhóm] Dataset & SDG** (50+ cases, Red Teaming) | 10 | Khánh chính, Khải hỗ trợ |
| **[Nhóm] Multi-Judge Consensus** (≥2 models, conflict logic) | 15 | Nhật chính |
| **[Nhóm] Regression Testing** (V1 vs V2, Release Gate) | 10 | Thành chính |
| **[Nhóm] Performance Async** (<2 phút, Cost report) | 10 | Tấn chính |
| **[Nhóm] Failure Analysis** (5 Whys, root cause) | 5 | Sơn chính |
| **[Cá nhân] Engineering Contribution** × 6 | 15 each | Tất cả |
| **[Cá nhân] Technical Depth** × 6 | 15 each | Tất cả |
| **[Cá nhân] Problem Solving** × 6 | 10 each | Tất cả |

> [!CAUTION]
> **ĐIỂM LIỆT:** Nhóm nào chỉ dùng 1 Judge hoặc thiếu Retrieval Metrics → phần nhóm **capped 30/60**.

---

## 🔴 GIAI ĐOẠN 0: Setup chung (Nhật - 15 phút đầu)

### Checklist:
- [ ] Clone repo, checkout branch `dev`
- [ ] Tạo file `.env` với các key: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- [ ] Tạo thư mục thiếu: `reports/`, `analysis/reflections/`
- [ ] Chạy `pip install -r requirements.txt` đảm bảo không lỗi
- [ ] Thêm dependencies còn thiếu vào `requirements.txt`:
  - `anthropic>=0.20.0` (cho Claude Judge)
  - `chromadb>=0.4.0` (cho VectorDB)
  - `aiohttp>=3.9.0`
- [ ] Commit cấu trúc ban đầu lên branch

```bash
mkdir -p reports analysis/reflections
touch analysis/reflections/.gitkeep
echo "anthropic>=0.20.0" >> requirements.txt
echo "chromadb>=0.4.0" >> requirements.txt
echo "aiohttp>=3.9.0" >> requirements.txt
pip install -r requirements.txt
```

---

## 🟡 THÀNH VIÊN 1: Lê Huy Hồng Nhật — Team Lead / Multi-Judge Engineer

> **File chính:** `engine/llm_judge.py`
> **Điểm nhóm:** 15 điểm (Multi-Judge Consensus)
> **Bắt đầu:** Sau setup → song song với Khánh & Khải

### 🎯 Nhiệm vụ cốt lõi
Implement **thực** `engine/llm_judge.py` gọi **2 model thật** (GPT-4o + Claude-3-5-sonnet), tính Agreement Rate bằng Cohen's Kappa, xử lý conflict tự động, và kiểm tra Position Bias.

### ✅ Checklist công việc

**Phần 1: Implement dual LLM Judge (60 phút)**
- [ ] Import `openai` và `anthropic` client, load `.env`
- [ ] Implement `_call_gpt_judge(question, answer, ground_truth)` → score 1-5 + reasoning + tokens
- [ ] Implement `_call_claude_judge(question, answer, ground_truth)` → score 1-5 + reasoning + tokens
- [ ] Viết rubric prompt chi tiết (Accuracy, Professionalism, Hallucination-free, Scale 1-5)
- [ ] Implement `evaluate_multi_judge()` gọi cả 2 bằng `asyncio.gather`
- [ ] Logic conflict: nếu `|score_GPT - score_Claude| > 1` → gọi GPT-4o làm "tie-breaker" lần 3
- [ ] Tính `agreement_rate` dùng **Cohen's Kappa** (không phải simple == check)
- [ ] Track `tokens_used` và `cost_usd` cho mỗi call

**Phần 2: Position Bias Check (30 phút)**
- [ ] Implement `check_position_bias(response_a, response_b)`:
  - Gọi Judge theo thứ tự (A, B)
  - Gọi lại theo thứ tự đảo (B, A)
  - Flag `has_position_bias=True` nếu kết quả lệch nhau
- [ ] Ghi kết quả bias vào output dictionary

**Phần 3: Integration & Testing (30 phút)**
- [ ] Test với 5 cases sau khi Khánh xong golden_set
- [ ] Đảm bảo `main.py` import và chạy được `MultiModelJudge` mới
- [ ] Verify output có đủ fields:
```json
{
  "final_score": 4.2,
  "agreement_rate": 0.85,
  "individual_scores": {"gpt-4o": 4, "claude-3-5-sonnet": 4.5},
  "reasoning": "GPT: ... Claude: ...",
  "conflict_resolved": false,
  "position_bias_detected": false,
  "cost_usd": 0.0023
}
```

### 📄 Reflection (`analysis/reflections/reflection_LeHuyHongNhat.md`)
- [ ] Giải thích Cohen's Kappa là gì và tại sao tốt hơn simple agreement rate
- [ ] Position Bias trong LLM Judge là gì và tác hại
- [ ] Trade-off: GPT-4o (đắt, chính xác) vs GPT-4o-mini (rẻ, nhanh)
- [ ] Vấn đề cụ thể gặp phải khi implement dual-API và cách fix

---

## 🟢 THÀNH VIÊN 2: Nguyễn Quốc Khánh — Data Engineer / SDG Lead

> **File chính:** `data/synthetic_gen.py`, `data/golden_set.jsonl`
> **Điểm nhóm:** 10 điểm (Dataset & SDG)
> **Bắt đầu:** Ngay từ đầu

> [!IMPORTANT]
> **⚡ CRITICAL PATH** — Mọi thành viên khác phụ thuộc vào file `data/golden_set.jsonl`. Hoàn thành ASAP!

### 🎯 Nhiệm vụ cốt lõi
Tạo **golden dataset ≥ 50 test cases** có `expected_retrieval_ids` (bắt buộc để tính Hit Rate), bao gồm 10 Red Teaming cases.

### ✅ Checklist công việc

**Phần 1: Thiết kế schema (15 phút)**
- [ ] Định nghĩa schema JSONL đầy đủ với mọi người:
```json
{
  "question": "...",
  "expected_answer": "...",
  "context": "...",
  "expected_retrieval_ids": ["doc_001", "doc_002"],
  "metadata": {
    "difficulty": "easy|medium|hard|adversarial",
    "type": "fact-check|reasoning|adversarial|edge-case",
    "category": "..."
  }
}
```
- [ ] Chuẩn bị ≥10 đoạn văn bản gốc source corpus (AI/Tech/Policy topic)
- [ ] Đặt tên `doc_id` theo format `doc_001`, `doc_002`, ... → **thông báo cho Khải** để agent dùng cùng ID

**Phần 2: Implement synthetic_gen.py (45 phút)**
- [ ] Implement `generate_qa_from_text()` gọi OpenAI API thật
- [ ] Prompt yêu cầu GPT trả về đúng JSON với `expected_retrieval_ids`
- [ ] Generate **40 regular cases** (easy/medium/hard)
- [ ] Generate **10 Red Teaming cases** theo `data/HARD_CASES_GUIDE.md`:
  - 3 Adversarial Prompts (Prompt Injection, Goal Hijacking)
  - 3 Edge Cases (Out of Context, Ambiguous, Conflicting Info)
  - 2 Multi-turn (Context carry-over)
  - 2 Technical (Latency Stress, Cost Efficiency)
- [ ] Script chạy ra đúng ≥50 lines trong `data/golden_set.jsonl`

**Phần 3: Validate & Notify (15 phút)**
- [ ] Viết hàm `validate_golden_set()` kiểm tra schema từng dòng
- [ ] Chạy: `python data/synthetic_gen.py` → verify ≥50 lines
- [ ] **Thông báo cho Nhật, Tấn, Khải** biết file đã sẵn sàng

### 📄 Reflection (`analysis/reflections/reflection_NguyenQuocKhanh.md`)
- [ ] Tại sao cần `expected_retrieval_ids` (liên hệ Hit Rate/MRR)
- [ ] Red Teaming là gì, tại sao quan trọng
- [ ] Circular evaluation problem: dùng LLM tạo dataset để đánh giá LLM
- [ ] Cách đảm bảo chất lượng Ground Truth trong SDG

---

## 🔵 THÀNH VIÊN 3: Nguyễn Tuấn Khải — Agent Engineer

> **File chính:** `agent/main_agent.py`, `agent/document_store.py` (mới)
> **Điểm nhóm:** Hỗ trợ Performance (10đ) + nâng chất benchmark
> **Bắt đầu:** Song song với Khánh (cần biết schema doc_id của Khánh trước)

### 🎯 Nhiệm vụ cốt lõi
Thay thế `MainAgent` mock bằng **RAG agent thực** với Vector DB, có `retrieved_ids` trong response để Retrieval Eval hoạt động.

### ✅ Checklist công việc

**Phần 1: Xây dựng Document Store (30 phút)**
- [ ] Tạo `agent/document_store.py` dùng ChromaDB (in-memory):
  - Load corpus từ danh sách documents cùng source với Khánh
  - `doc_id` phải khớp với `expected_retrieval_ids` của Khánh (**sync với Khánh**)
  - Implement `retrieve(query, top_k=5)` → list `(doc_id, content, score)`

**Phần 2: Upgrade MainAgent (45 phút)**
- [ ] Implement `MainAgent.query()` thực:
  ```python
  async def query(self, question: str) -> Dict:
      retrieved = self.doc_store.retrieve(question, top_k=5)
      retrieved_ids = [r["doc_id"] for r in retrieved]
      contexts = [r["content"] for r in retrieved]
      # Call OpenAI gpt-4o-mini với context
      ...
      return {
          "answer": "...",
          "contexts": contexts,
          "retrieved_ids": retrieved_ids,  # ⚡ BẮT BUỘC cho Hit Rate
          "metadata": {"model": "gpt-4o-mini", "tokens_used": ..., "cost_usd": ...}
      }
  ```
- [ ] Tạo **Agent V1** (system prompt đơn giản, chunk size lớn 500 tokens)
- [ ] Tạo **Agent V2** (system prompt chi tiết, chunk size nhỏ 200 tokens + basic reranking)
- [ ] Đảm bảo `retrieved_ids` được trả về đúng format

**Phần 3: Testing (15 phút)**
- [ ] Test thủ công 5 câu hỏi mẫu
- [ ] Verify `retrieved_ids` khớp một số `expected_retrieval_ids` trong dataset
- [ ] Đo latency mỗi query < 3 giây

### 📄 Reflection (`analysis/reflections/reflection_NguyenTuanKhai.md`)
- [ ] RAG architecture: tại sao Retrieval trước, Generation sau
- [ ] Chunking strategy: Fixed-size vs Semantic — trade-offs
- [ ] Tại sao V2 tốt hơn V1 với số liệu từ benchmark
- [ ] Vấn đề gặp khi connect Vector DB với async agent

---

## 🟠 THÀNH VIÊN 4: Phan Văn Tấn — Async Performance Engineer

> **File chính:** `engine/retrieval_eval.py`, `engine/runner.py`
> **Điểm nhóm:** 10đ (Retrieval Eval) + 10đ (Performance Async) = **20 điểm**
> **Bắt đầu:** Sau khi Khánh commit golden_set ≈ T+45 phút

### 🎯 Nhiệm vụ cốt lõi
1. Implement **Retrieval Evaluator thực** tính Hit Rate + MRR đúng cho 50 cases
2. Nâng cấp **BenchmarkRunner** chạy song song < 2 phút với Cost Report

### ✅ Checklist công việc

**Phần 1: Nâng cấp Retrieval Evaluator (30 phút)**
- [ ] `calculate_hit_rate()`: kiểm tra `expected_retrieval_ids ∩ retrieved_ids[:top_k]`
- [ ] `calculate_mrr()`: tìm rank đầu tiên của expected_id → MRR = 1/rank
- [ ] Implement `evaluate_batch()` thực sự (xóa placeholder):
  ```python
  async def evaluate_batch(self, dataset, agent_responses):
      results = []
      for case, resp in zip(dataset, agent_responses):
          hit = self.calculate_hit_rate(case["expected_retrieval_ids"], resp["retrieved_ids"])
          mrr = self.calculate_mrr(case["expected_retrieval_ids"], resp["retrieved_ids"])
          results.append({"hit_rate": hit, "mrr": mrr, "question": case["question"]})
      return {
          "avg_hit_rate": mean(r["hit_rate"] for r in results),
          "avg_mrr": mean(r["mrr"] for r in results),
          "per_case": results
      }
  ```
- [ ] Verify với 5 sample cases thủ công

**Phần 2: Nâng cấp BenchmarkRunner (45 phút)**
- [ ] Thêm `asyncio.Semaphore(5)` để giới hạn concurrent calls
- [ ] Implement Cost Tracking: cộng `cost_usd` từ agent + judge mỗi case
- [ ] Thêm progress bar `tqdm`
- [ ] Đo `total_time_seconds` bao ngoài toàn bộ `run_all()`
- [ ] Thêm Cost Report vào summary:
  ```json
  "performance": {
    "total_time_seconds": 87.3,
    "avg_latency_per_case": 1.75,
    "total_cost_usd": 0.42,
    "cost_per_case_usd": 0.0084
  }
  ```
- [ ] Đảm bảo 50 cases chạy trong **< 120 giây**

**Phần 3: Testing (15 phút)**
- [ ] Chạy với 10 cases test trước khi chạy full 50
- [ ] Verify Hit Rate và MRR có giá trị thực (không phải 0.85/0.72 placeholder)
- [ ] Verify total_time < 120s

### 📄 Reflection (`analysis/reflections/reflection_PhanVanTan.md`)
- [ ] MRR là gì — ví dụ cụ thể với số liệu
- [ ] Tại sao Retrieval Quality → Answer Quality (với bằng chứng từ kết quả)
- [ ] `asyncio.gather` vs `asyncio.Semaphore` — khi nào dùng cái gì
- [ ] 3 cách giảm 30% chi phí eval mà không giảm accuracy

---

## 🟣 THÀNH VIÊN 5: Lê Công Thành — DevOps / Regression Gate Engineer

> **File chính:** `main.py` (mở rộng Regression Logic)
> **Điểm nhóm:** 10 điểm (Regression Testing)
> **Bắt đầu:** Sau khi Tấn xong runner.py ≈ T+90 phút

### 🎯 Nhiệm vụ cốt lõi
Implement **Release Gate tự động multi-criteria** và đảm bảo `summary.json` có đầy đủ fields.

### ✅ Checklist công việc

**Phần 1: Release Gate logic (45 phút)**
- [ ] Implement `compare_versions(v1_summary, v2_summary)`:
  ```python
  {
    "score_delta": +0.3,
    "hit_rate_delta": +0.05,
    "cost_delta": -0.02,    # âm = rẻ hơn = tốt
    "latency_delta": -2.1,  # âm = nhanh hơn = tốt
    "decision": "APPROVE | WARN | BLOCK",
    "reasons": ["Score tăng 0.3", "Cost giảm 4.7%"]
  }
  ```
- [ ] Implement **multi-criteria Release Gate**:
  - `APPROVE`: `score_delta >= 0` AND `cost_delta <= 0.1` AND `hit_rate_delta >= -0.05`
  - `BLOCK`: `score_delta < -0.2` OR `hit_rate_delta < -0.1`
  - `WARN`: các trường hợp còn lại
- [ ] Ghi `reports/regression_report.json` đầy đủ
- [ ] Mô phỏng V2 thực sự khác V1 (thay đổi system prompt hoặc chunk size)

**Phần 2: Hoàn thiện summary.json (30 phút)**
- [ ] Đảm bảo đủ các fields mà `check_lab.py` kiểm tra:
  ```json
  {
    "metadata": {
      "version": "Agent_V2_Optimized",
      "total": 50,
      "timestamp": "...",
      "regression": {"v1_score": 3.8, "v2_score": 4.1, "decision": "APPROVE"}
    },
    "metrics": {
      "avg_score": 4.1,
      "hit_rate": 0.82,
      "mrr": 0.71,
      "agreement_rate": 0.85,
      "total_cost_usd": 0.42,
      "total_time_seconds": 87.3
    }
  }
  ```
- [ ] Chạy `python check_lab.py` → **chỉ thấy ✅, không có ❌ hoặc ⚠️**

**Phần 3: End-to-End test (15 phút)**
- [ ] Chạy toàn bộ pipeline:
  ```bash
  python data/synthetic_gen.py && python main.py && python check_lab.py
  ```
- [ ] Capture output dán vào reflection

### 📄 Reflection (`analysis/reflections/reflection_LeCongThanh.md`)
- [ ] Regression Testing trong AI/ML vs Software Testing truyền thống
- [ ] Tại sao Release Gate cần multi-criteria (không chỉ xem score)
- [ ] Goodhart's Law trong AI evaluation là gì
- [ ] Cách integrate Release Gate này vào GitHub Actions CI/CD

---

## ⚫ THÀNH VIÊN 6: Nguyễn Quế Sơn — Analyst / 5 Whys Expert

> **File chính:** `analysis/failure_analysis.md`
> **Điểm nhóm:** 5 điểm (Failure Analysis)
> **Bắt đầu:** Sau khi có kết quả benchmark ≈ T+150 phút

### 🎯 Nhiệm vụ cốt lõi
Viết **báo cáo phân tích thất bại sâu** với 5 Whys methodology, chỉ ra lỗi hệ thống (Chunking, Ingestion, v.v).

### ✅ Checklist công việc

**Phần 1: Phân tích kết quả (30 phút)**
- [ ] Đọc `reports/benchmark_results.json` — tìm cases có `status: "fail"`
- [ ] Đọc `reports/summary.json` — ghi nhận metrics tổng quan
- [ ] Phân loại lỗi thành nhóm:
  - Hallucination (agent bịa thông tin)
  - Incomplete (thiếu thông tin quan trọng)
  - Tone Mismatch (ngôn ngữ không phù hợp)
  - Out-of-Context Error (không nhận ra câu hỏi ngoài scope)
  - Adversarial Failure (bị Prompt Injection)

**Phần 2: Viết Failure Analysis Report (60 phút)**
- [ ] Điền đầy đủ `analysis/failure_analysis.md`:
  - **Section 1:** Tổng quan benchmark với số liệu thực
  - **Section 2:** Failure Clustering table với số liệu thực
  - **Section 3:** Phân tích 5 Whys cho **ít nhất 3 case tệ nhất**
    - Mỗi case phải đủ 5 tầng Why
    - Root Cause phải cụ thể: "Chunk size 1000 tokens quá lớn làm loãng thông tin bảng số liệu"
  - **Section 4:** Action Plan ≥ 5 items cụ thể, đo lường được
- [ ] Độ dài tối thiểu: 600 từ

**Phần 3: (Optional Bonus) Analysis Script (30 phút)**
- [ ] Tạo `analysis/clustering.py`: đọc JSON, group failures, output thống kê
- [ ] Script này cho thấy Engineering Contribution rõ ràng

### 📄 Reflection (`analysis/reflections/reflection_NguyenQueSon.md`)
- [ ] 5 Whys methodology — ứng dụng trong Root Cause Analysis
- [ ] Failure Mode tìm ra: liên hệ thế nào với Chunking/Ingestion/Retrieval/Prompting
- [ ] Đề xuất kỹ thuật cụ thể để giảm Hallucination
- [ ] Scale: nếu có 1000 cases thì phân tích failure như thế nào?

---

## 📋 CHECKLIST CUỐI CÙNG (Nhật review trước khi nộp)

### Code & Files
- [ ] `data/synthetic_gen.py` chạy được, tạo `data/golden_set.jsonl` ≥ 50 lines
- [ ] `agent/main_agent.py` trả về `retrieved_ids` trong response
- [ ] `engine/llm_judge.py` gọi 2 model thật, có `agreement_rate` (Claude + GPT)
- [ ] `engine/retrieval_eval.py` tính Hit Rate & MRR thực (không placeholder)
- [ ] `engine/runner.py` chạy song song Semaphore, có Cost tracking
- [ ] `main.py` có Release Gate multi-criteria V1 vs V2

### Reports (Auto-generated)
- [ ] `reports/summary.json` tồn tại, đúng format
- [ ] `reports/benchmark_results.json` tồn tại
- [ ] `reports/regression_report.json` tồn tại
- [ ] `analysis/failure_analysis.md` điền đầy đủ (không còn placeholder)

### Individual Reflections (6 files)
- [ ] `analysis/reflections/reflection_LeHuyHongNhat.md`
- [ ] `analysis/reflections/reflection_NguyenQuocKhanh.md`
- [ ] `analysis/reflections/reflection_NguyenTuanKhai.md`
- [ ] `analysis/reflections/reflection_PhanVanTan.md`
- [ ] `analysis/reflections/reflection_LeCongThanh.md`
- [ ] `analysis/reflections/reflection_NguyenQueSon.md`

### Validation bắt buộc
- [ ] `python data/synthetic_gen.py` → thành công, ≥ 50 cases
- [ ] `python main.py` → thành công, tạo reports/, in "CHẤP NHẬN" hoặc "TỪ CHỐI"
- [ ] `python check_lab.py` → **CHỈ thấy ✅, không có ❌ hoặc ⚠️**
- [ ] `.env` không được commit (có trong `.gitignore`)
- [ ] Mỗi người có ít nhất 1 Git commit độc lập vào file của mình

---

## ⏱️ Timeline 4 Giờ Chi Tiết

| Thời điểm | Nhật (Lead) | Khánh (Data) | Khải (Agent) | Tấn (Perf) | Thành (Regression) | Sơn (Analysis) |
|---|---|---|---|---|---|---|
| **T+0:00** | Setup repo, .env, thư mục | Thiết kế schema, sync với Khải | Sync doc_id với Khánh | Đọc code runner.py | Đọc code main.py | Đọc rubric kỹ |
| **T+0:30** | Implement GPT Judge | Generate QA pairs (LLM call) | Setup ChromaDB | — | — | Chuẩn bị template |
| **T+1:00** | Implement Claude Judge | Tạo Red Teaming cases | Implement retrieve() + V1 | ⚡ **Start**: Nâng cấp retrieval_eval | — | — |
| **T+1:30** | Conflict resolution + Kappa | ✅ **Done** → commit! | Implement Agent V2 | Nâng cấp Runner + Semaphore | ⚡ **Start**: Release Gate | — |
| **T+2:00** | Position Bias check | Viết reflection | Testing agent | Cost tracking + tqdm | Compare V1 vs V2 | — |
| **T+2:30** | Integration test | — | ✅ **Done** → commit! | ✅ **Done** → commit! | Fix summary.json | ⚡ **Start**: đọc results |
| **T+3:00** | ✅ **Done** → commit! | — | — | — | End-to-end test | 5 Whys analysis |
| **T+3:30** | Review toàn team | Reflection | Reflection | Reflection | ✅ **Done** → commit! | ✅ **Done** → commit! |
| **T+4:00** | **`check_lab.py` FINAL** | — | — | — | — | Reflection done |

---

## 🔑 Dependency Gates

```
Khánh commit golden_set.jsonl schema
      │
      ├──► Khải: biết doc_id format → implement agent/document_store.py
      │
      └──► Tấn: biết schema → viết evaluate_batch() đúng field names
                    │
                    └──► Thành: runner.py ổn → chạy main.py regression
                                    │
                                    └──► Sơn: có reports/ → phân tích 5 Whys

[Độc lập hoàn toàn]
Nhật: engine/llm_judge.py không phụ thuộc ai
```

---

## 💡 Commit Convention (Bắt buộc cho điểm Engineering Contribution)

```bash
# Mỗi người dùng commit message rõ ràng:
git commit -m "feat(judge): implement real GPT+Claude dual judge with Cohen's Kappa"     # Nhật
git commit -m "feat(data): generate 50 golden cases with 10 red teaming scenarios"     # Khánh
git commit -m "feat(agent): add ChromaDB retrieval, return retrieved_ids for eval"     # Khải
git commit -m "feat(eval): implement real hit_rate and mrr, async runner with cost"    # Tấn
git commit -m "feat(regression): multi-criteria release gate V1 vs V2 comparison"     # Thành
git commit -m "docs(analysis): complete 5-whys failure analysis with root cause"       # Sơn
```

> [!WARNING]
> **Không ai được commit chung một file** — mỗi người phải có commit độc lập vào file của mình để `git log` chứng minh contribution cho giám khảo.

---

*Kế hoạch tạo lúc: 2026-04-21 | Nhóm C401-D6*
