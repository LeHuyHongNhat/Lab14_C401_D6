# Reflection — Nguyễn Tuấn Khải
> **Vai trò:** Agent Engineer | **Lab:** 14 — AI Evaluation Factory | **Nhóm:** C401-D6

---

## 1. Công việc cá nhân

### Phạm vi trách nhiệm
- **File chính:** `agent/main_agent.py`, `agent/document_store.py` (file mới tạo)
- **Đóng góp nhóm:** Cung cấp `retrieved_ids` trong mỗi response để Retrieval Evaluator (Tấn) tính Hit Rate và MRR
- **Dependencies:** Sync `doc_id` format với Khánh trước khi code → dùng đúng `doc_001`–`doc_010` từ `source_corpus.json`

### Những gì đã implement

**`agent/document_store.py`** — Vector store in-memory:
- ChromaDB client với OpenAI `text-embedding-3-small` (thay thế DefaultEmbeddingFunction vì lỗi timeout khi tải model ONNX 79MB)
- Fixed-size chunking: mỗi document được split thành các chunk theo token size (V1=500, V2=200), overlap 50 tokens
- Chunk ID dạng `doc_001_c0`, `doc_001_c1`... được map về parent `doc_id` khi trả kết quả, đảm bảo khớp với `expected_retrieval_ids` trong golden dataset
- `retrieve(query, top_k)` → dedup theo parent doc_id, trả về list `{doc_id, content, score, title}`

**`agent/main_agent.py`** — RAG Agent thực (thay thế mock):
- **Agent V1:** `chunk_size=500`, top_k=5, system prompt đơn giản
- **Agent V2:** `chunk_size=200`, top_k=3 + keyword-overlap reranking, system prompt chi tiết với rule chống adversarial
- Retry tự động với exponential backoff khi gặp `RateLimitError`
- Gọi `gpt-4o-mini` với context từ ChromaDB, response bắt buộc có `retrieved_ids`

### Vấn đề gặp phải và cách fix

**Vấn đề 1:** ChromaDB `DefaultEmbeddingFunction` cố tải model ONNX 79MB từ internet nhưng bị `ReadTimeout` do mạng không ổn định.

**Cách fix:** Chuyển sang `OpenAIEmbeddingFunction` với `text-embedding-3-small` — gọi thẳng qua API key có sẵn, không cần download bất kỳ file nào về local.

**Vấn đề 2:** Merge conflict trong `engine/runner.py` do 2 nhánh cùng sửa file, gây `SyntaxError` khi chạy `main.py`.

**Cách fix:** Resolve conflict thủ công, giữ lại phiên bản đúng indent (code nằm trong `async with self.semaphore` block) và cách lấy `cost_usd` từ `response["metadata"]`.

---

## 2. Câu hỏi reflection kỹ thuật

### 1. RAG architecture: tại sao Retrieval trước, Generation sau?

LLM có hai hạn chế cơ bản: **knowledge cutoff** (không biết thông tin sau ngày huấn luyện) và **hallucination** (bịa thông tin khi không chắc). RAG giải quyết cả hai bằng cách inject grounding facts từ corpus thực vào context trước khi generation. Model không cần "nhớ" thông tin — nó chỉ cần tổng hợp từ những đoạn văn bản được cung cấp. Nếu làm ngược (generation trước, retrieval sau) thì không có ý nghĩa vì LLM cần context để trả lời đúng ngay từ đầu.

### 2. Chunking strategy: Fixed-size vs Semantic — trade-offs?

| | Fixed-size (V1=500, V2=200 tokens) | Semantic chunking |
|---|---|---|
| **Ưu điểm** | Đơn giản, nhanh, dễ implement | Giữ nguyên nghĩa, không cắt đứt giữa câu |
| **Nhược điểm** | Có thể cắt đứt ý giữa chừng, mất context | Phức tạp hơn, tốn 2-3x thời gian ingestion |
| **Phù hợp** | Văn bản đồng nhất (news, FAQ) | Văn bản kỹ thuật, bảng số liệu, multi-topic |

Trong project này dùng fixed-size với 2 kích thước khác nhau để so sánh V1 vs V2. Chunk nhỏ hơn (200 tokens) giúp retrieval chính xác hơn nhưng mỗi chunk có ít context hơn khi đưa vào LLM. Với corpus lớn hơn, "parent-child chunking" (chunk nhỏ để retrieve, chunk lớn để generate) là lựa chọn tốt nhất để cân bằng cả hai.

### 3. Tại sao V2 tốt hơn hoặc kém hơn V1? Số liệu thực từ benchmark (sau khi có chunking):

| Metric | V1 (chunk=500) | V2 (chunk=200) | Delta |
|---|---|---|---|
| Avg Score (LLM Judge) | **4.62** | 4.51 | -0.12 |
| Hit Rate | **0.98** | **0.98** | 0.00 |
| MRR | **0.960** | 0.943 | -0.017 |
| Agreement Rate | **0.944** | 0.918 | -0.026 |
| Cost/case | $0.0024 | **$0.0023** | -$0.0001 |
| Total Time | **44.1s** | 51.2s | +7.1s |

**Nhận xét:** Với chunking thực, V2 vẫn có score thấp hơn V1 dù chunk nhỏ hơn → Release Gate ra quyết định **WARN** (cải thiện so với BLOCK trước đó). Lý do V2 không vượt V1 là keyword reranking không chính xác về mặt ngữ nghĩa: nó ưu tiên chunk có nhiều từ trùng với query nhưng chunk đó chưa chắc chứa thông tin liên quan nhất. Hướng cải thiện: dùng cross-encoder reranking hoặc MMR (Maximal Marginal Relevance) để đa dạng hóa context thay vì chỉ dựa vào từ khóa.

### 4. Vấn đề khi connect Vector DB với async agent?

ChromaDB in-memory client không có vấn đề với asyncio vì các thao tác embedding và query là synchronous — chúng chạy trong thread riêng và không block event loop của asyncio. Tuy nhiên, nếu ChromaDB được dùng với persistent client (lưu ra disk), cần lưu ý:

- **Không dùng chung 1 collection object** giữa nhiều coroutine đồng thời — ChromaDB không thread-safe cho writes
- **Giải pháp:** Khởi tạo DocumentStore 1 lần duy nhất trong `__init__` của agent, không tạo mới mỗi query
- **Trong project này:** `BenchmarkRunner` khởi tạo 1 `MainAgent` rồi gọi `query()` nhiều lần — pattern này an toàn vì ChromaDB chỉ đọc (read-only) sau khi corpus đã được load

---

## 3. Tóm tắt công việc nhóm

### Pipeline 4 giai đoạn

```
[GĐ1 — Song song]
  Khánh → Tạo 50+ golden test cases (data/golden_set.jsonl)
  Khải  → Xây RAG agent thực (agent/)

[GĐ2 — Phụ thuộc GĐ1]
  Nhật  → Dual LLM Judge: GPT-4o + Gemini, tính Cohen's Kappa
  Tấn   → Retrieval Eval (Hit Rate, MRR) + Async Runner

[GĐ3 — Phụ thuộc GĐ2]
  Thành → Regression Release Gate: V1 vs V2 → WARN
  Sơn   → Phân tích 5 Whys từ kết quả benchmark

[GĐ4]
  Mọi người → Reflection cá nhân
```

### Kết quả benchmark cuối (V2 — 50 test cases)

| Metric | Giá trị |
|---|---|
| Avg LLM Judge Score | 4.51 / 5.0 |
| Hit Rate | 98% |
| MRR | 0.943 |
| Agreement Rate | 0.918 |
| Total Cost | $0.1134 |
| Total Time | 51.2s |
| Release Gate | WARN |

---

*Nguyễn Tuấn Khải — C401-D6 — Lab 14 — 2026-04-21*
