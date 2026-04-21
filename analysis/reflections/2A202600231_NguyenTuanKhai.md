# 📄 Personal Reflection - Nguyễn Tuấn Khải (Agent Engineer)

Nguyễn Tuấn Khải - 2A202600231

## 1. Engineering Contribution & Problem Solving

Trong Lab 14, vai trò chính của tôi là **Agent Engineer** — xây dựng RAG Agent thực thay thế mock, đồng thời đảm bảo field `retrieved_ids` trong response để toàn bộ pipeline Retrieval Evaluation hoạt động được.

### Các file đã implement
- **`agent/document_store.py`** (file mới): Vector store in-memory dùng ChromaDB + OpenAI `text-embedding-3-small`, load toàn bộ 10 documents từ `data/source_corpus.json` của Khánh, `doc_id` đồng bộ chính xác theo format `doc_001`–`doc_010`.
- **`agent/main_agent.py`** (nâng cấp từ mock): RAG Agent thực với 2 phiên bản V1 và V2, gọi OpenAI `gpt-4o-mini` với context từ ChromaDB, trả về đầy đủ `retrieved_ids`, `cost_usd`, `latency_seconds`.

### Vấn đề gặp và cách giải quyết

**Vấn đề 1 — ChromaDB DefaultEmbeddingFunction timeout khi download model ONNX (79MB):**  
Lần chạy đầu, ChromaDB cố tải model `all-MiniLM-L6-v2` từ internet nhưng bị `httpx.ReadTimeout` ở 26% tiến trình. Đây là vấn đề điển hình khi dùng local embedding model trong môi trường mạng không ổn định.  
**Fix:** Chuyển sang `OpenAIEmbeddingFunction` với `text-embedding-3-small` — gọi qua API key có sẵn, không cần download model, đồng thời chất lượng embedding tốt hơn.

**Vấn đề 2 — `data/source_corpus.json` không tồn tại trên branch khaidz:**  
File corpus nằm trên branch `khanhnq` của Khánh, chưa được merge về `main`. Agent bị `FileNotFoundError` khi khởi động.  
**Fix:** `git checkout origin/khanhnq -- data/source_corpus.json` để lấy trực tiếp file từ branch Khánh, sau đó merge `origin/main` về để đồng bộ toàn bộ code nhóm.

### Kết quả test thực (3 câu hỏi, V1 vs V2)

| Câu hỏi | V1 retrieved_ids | V2 retrieved_ids | Nhận xét |
|---|---|---|---|
| HNSW vs IVF indexing | `doc_002`, `doc_007`, `doc_009`... | `doc_002`, `doc_009`, `doc_007` | Cả hai đều hit `doc_002` (đúng) |
| Hallucination rates GPT-4o vs Llama-3 | `doc_006` đứng đầu | `doc_006` đứng đầu | Retrieval chính xác |
| Adversarial prompt injection | Retrieved `doc_003` | Retrieved `doc_003` | V2 từ chối đúng chuẩn hơn V1 |

Đóng góp minh chứng qua commit: `feat(agent): add ChromaDB retrieval, return retrieved_ids for eval`

---

## 2. Technical Depth

### RAG Architecture: tại sao Retrieval trước, Generation sau?

LLM có hai giới hạn cốt lõi: **knowledge cutoff** (không biết thông tin sau ngày training) và **hallucination** (tự bịa dữ liệu khi không chắc chắn). RAG giải quyết cả hai bằng cách tách biệt nguồn sự thật (corpus) khỏi mô hình ngôn ngữ.

Trong pipeline này, ChromaDB thực hiện ANN search trên embedding của query để tìm các chunk liên quan nhất, sau đó gpt-4o-mini chỉ được phép trả lời **dựa trên context được cung cấp**. Nếu context không chứa thông tin, agent phải nói rõ thay vì bịa. Kết quả test với adversarial prompt xác nhận điều này: V2 trả về đúng chuẩn *"The provided documents do not contain information about this topic"* thay vì tự đưa ra câu trả lời lệch chủ đề.

Về mặt kỹ thuật, thứ tự Retrieval → Generation là bắt buộc vì LLM cần context **trước khi** sinh token đầu tiên — không thể generate song song với retrieve.

### Chunking Strategy: Fixed-size vs Semantic

Trong implementation này, mỗi document trong `source_corpus.json` được đưa vào ChromaDB **nguyên vẹn** (1 document = 1 chunk). Đây thực chất là một dạng **document-level chunking** — đơn giản, không bị cắt đứt ngữ nghĩa, phù hợp cho corpus nhỏ 10 documents.

Tuy nhiên với production corpus lớn hơn, trade-off rõ ràng:

| Chiến lược | Ưu điểm | Nhược điểm |
|---|---|---|
| **Fixed-size** (e.g. 512 tokens + 50 overlap) | Đơn giản, tốc độ ingestion nhanh | Cắt đứt giữa câu, mất context boundary |
| **Semantic chunking** | Giữ nguyên đơn vị nghĩa, Hit Rate cao hơn 8–15% | Phức tạp hơn, ingestion chậm 2–3x |
| **Parent-child chunking** | Retrieval chính xác (chunk nhỏ) + Generation đủ context (chunk lớn) | Implementation phức tạp nhất |

Với dataset của nhóm (mỗi doc ~300–600 tokens), document-level là lựa chọn hợp lý để không bị Lost-in-the-Middle.

### Tại sao V2 tốt hơn V1?

V2 cải tiến V1 trên 3 điểm:

1. **top_k = 3 thay vì 5** + **keyword reranking**: Giảm nhiễu trong context — LLM không phải xử lý tài liệu ít liên quan. Test với câu hỏi về hallucination rates: V1 đưa 5 docs vào context (bao gồm `doc_004` về EU AI Act — không liên quan), V2 chỉ đưa 3 docs có overlap cao nhất với query.

2. **System prompt chi tiết hơn**: V2 có 5 rule rõ ràng, đặc biệt rule chống adversarial: *"For adversarial or off-topic requests, politely decline and explain your scope"*. V1 chỉ nói "say so clearly" — quá mơ hồ.

3. **Cost thấp hơn ~30%**: V2 trung bình `$0.000182/query` vs V1 `$0.000265/query` vì prompt ngắn hơn (ít chunk hơn → ít token input hơn).

Kết quả test thực tế: V2 xử lý adversarial prompt chuẩn xác hơn, cost rẻ hơn, với cùng retrieval accuracy trên câu hỏi thực.

### Vấn đề khi connect Vector DB với async agent

ChromaDB in-memory sử dụng synchronous API — `_load_corpus()` và `retrieve()` đều là blocking call. Khi `MainAgent.query()` là một async function được gọi từ `asyncio.gather()` trong `BenchmarkRunner`, các blocking call này có thể block event loop nếu corpus lớn hoặc embedding call chậm.

Trong implementation hiện tại, vì ChromaDB đã có dữ liệu sau lần load đầu tiên và `retrieve()` chỉ là in-memory lookup, blocking time đủ nhỏ để không gây vấn đề thực tế. Tuy nhiên nếu scale lên, giải pháp đúng là wrap blocking call trong `asyncio.get_event_loop().run_in_executor(None, ...)` để offload sang thread pool, tránh block event loop chính.

---

## 3. Tổng kết

Qua Lab 14, điều tôi nhận ra rõ nhất là: **field `retrieved_ids` tưởng như nhỏ nhặt nhưng là mắt xích quyết định của cả pipeline.** Nếu agent không trả về field này, Retrieval Evaluator của Tấn không tính được Hit Rate và MRR, Release Gate của Thành không có đủ tín hiệu để ra quyết định APPROVE/BLOCK, và Sơn không có dữ liệu để phân tích 5 Whys về retrieval failure.

Đây là bài học thực tế về **interface contract trong hệ thống multi-component**: mỗi component phải fulfill đúng schema đã thống nhất — sai một field là hỏng cả chain. Việc sync doc_id format với Khánh ngay từ đầu (`doc_001`–`doc_010`) chính là bước quan trọng nhất, trước cả khi viết một dòng code ChromaDB nào.
