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
- Load toàn bộ 10 documents từ `data/source_corpus.json`, `doc_id` khớp chính xác với `expected_retrieval_ids` trong golden dataset
- `retrieve(query, top_k)` → trả về list `{doc_id, content, score, title}`

**`agent/main_agent.py`** — RAG Agent thực (thay thế mock):
- **Agent V1:** top_k=5, system prompt đơn giản
- **Agent V2:** top_k=3 + keyword-overlap reranking, system prompt chi tiết với rule chống adversarial
- Gọi `gpt-4o-mini` với context từ ChromaDB
- Response bắt buộc có `retrieved_ids` để unlock Hit Rate & MRR cho pipeline

### Vấn đề gặp phải và cách fix

**Vấn đề:** ChromaDB `DefaultEmbeddingFunction` cố tải model ONNX 79MB từ internet nhưng bị `ReadTimeout` do mạng không ổn định.

**Cách fix:** Chuyển sang `OpenAIEmbeddingFunction` với `text-embedding-3-small` — gọi thẳng qua API key có sẵn, không cần download bất kỳ file nào về local. Chi phí embedding 10 documents ~$0.00002, hoàn toàn không đáng kể.

---

## 2. Câu hỏi reflection kỹ thuật

### 1. RAG architecture: tại sao Retrieval trước, Generation sau?

LLM có hai hạn chế cơ bản: **knowledge cutoff** (không biết thông tin sau ngày huấn luyện) và **hallucination** (bịa thông tin khi không chắc). RAG giải quyết cả hai bằng cách inject grounding facts từ corpus thực vào context trước khi generation. Model không cần "nhớ" thông tin — nó chỉ cần tổng hợp từ những đoạn văn bản được cung cấp. Nếu làm ngược (generation trước, retrieval sau) thì không có ý nghĩa vì LLM cần context để trả lời đúng ngay từ đầu.

### 2. Chunking strategy: Fixed-size vs Semantic — trade-offs?

| | Fixed-size (500 tokens) | Semantic chunking |
|---|---|---|
| **Ưu điểm** | Đơn giản, nhanh, dễ implement | Giữ nguyên nghĩa, không cắt đứt giữa câu |
| **Nhược điểm** | Có thể cắt đứt ý giữa chừng, mất context | Phức tạp hơn, tốn 2-3x thời gian ingestion |
| **Phù hợp** | Văn bản đồng nhất (news, FAQ) | Văn bản kỹ thuật, bảng số liệu, multi-topic |

Trong project này dùng fixed-size (toàn bộ document là 1 chunk) vì corpus chỉ có 10 documents, mỗi document đủ nhỏ để fit vào context window. Với corpus lớn hơn, semantic chunking hoặc "parent-child chunking" (small chunk để retrieve, large chunk để generate) sẽ cho kết quả tốt hơn.

### 3. Tại sao V2 tốt hơn hoặc kém hơn V1? Số liệu thực từ benchmark:

| Metric | V1 (Base) | V2 (Optimized) | Delta |
|---|---|---|---|
| Avg Score (LLM Judge) | **4.44** | 4.16 | **-0.28** |
| Hit Rate | 0.94 | **0.96** | +0.02 |
| MRR | **0.935** | 0.90 | -0.035 |
| Cost/case | $0.0041 | **$0.0038** | -$0.0003 |
| Avg Latency | 2.71s | **2.56s** | -0.15s |

**Nhận xét:** V2 có Hit Rate cao hơn nhưng score tổng thể thấp hơn V1 → Release Gate ra quyết định **BLOCK**. Nguyên nhân có thể là keyword reranking của V2 đôi khi ưu tiên documents có nhiều từ khóa trùng nhau nhưng ít liên quan về mặt ngữ nghĩa, dẫn đến context kém chất lượng hơn. Đây là điểm cần cải thiện — nên dùng cross-encoder reranking thay vì keyword overlap để đánh giá relevance chính xác hơn.

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
  Nhật  → Dual LLM Judge: GPT-4o + Claude, tính Cohen's Kappa
  Tấn   → Retrieval Eval (Hit Rate, MRR) + Async Runner

[GĐ3 — Phụ thuộc GĐ2]
  Thành → Regression Release Gate: V1 vs V2 → BLOCK
  Sơn   → Phân tích 5 Whys từ kết quả benchmark

[GĐ4]
  Mọi người → Reflection cá nhân
```

### Kết quả benchmark cuối (V2 — 50 test cases)

| Metric | Giá trị |
|---|---|
| Avg LLM Judge Score | 4.16 / 5.0 |
| Hit Rate | 96% |
| MRR | 0.90 |
| Agreement Rate (Cohen's Kappa) | 0.9319 |
| Total Cost | $0.1924 |
| Total Time | 978.71s (~16 phút) |

---

*Nguyễn Tuấn Khải — C401-D6 — Lab 14 — 2026-04-21*
