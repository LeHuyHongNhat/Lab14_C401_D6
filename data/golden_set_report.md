# 📊 Báo cáo Phân tích Chiến lược Golden Dataset (Lab 14)

Báo cáo này đánh giá 3 phiên bản dữ liệu mẫu dựa trên **Grading Rubric (Expert Level)** của Lab 14 nhằm giúp team lựa chọn bộ dữ liệu tối ưu nhất để đạt điểm 100/100.

---

## 🔝 1. Phân tích theo Rubric Chấm điểm

| Tiêu chuẩn Rubric | GPT-4o (Original) | Gemini 2.5 Pro | Claude (Hand-crafted) |
| :--- | :---: | :---: | :---: |
| **Số lượng ≥ 50 cases** | ✅ 50 cases | ❌ 30 cases | ✅ **50 cases** |
| **Ground Truth IDs mapping** | ✅ Đầy đủ | ✅ Đầy đủ | ✅ **Đầy đủ** |
| **Red Teaming (Adversarial)** | ⚠️ 10 (Cơ bản) | ⚠️ 6 (Cơ bản) | ✅ **12 (Nâng cao)** |
| **Retrieval Eval (Hit/MRR)** | ⚠️ Easy (Hit@1) | ⚠️ Easy | ✅ **Hard (Hit@2-3)** |
| **Phân tích "5 Whys" potential**| Thấp (Ít lỗi) | Trung bình | **Rất cao (Nhiều bẫy)** |

### 🎯 Đánh giá khả năng đạt điểm:
*   **GPT-4o:** Đảm bảo điểm sàn (7-8đ phần Dataset). Khó lấy điểm tối đa phần "Giải thích mối liên hệ Retrieval vs Answer Quality" vì câu hỏi quá dễ, chỉ cần 1 doc là trả lời được.
*   **Claude (Hand-crafted):** **Khả năng đạt 10/10 tuyệt đối.** Các câu hỏi Multi-hop buộc Agent phải retrieve đúng 2-3 tài liệu. Nếu Agent chỉ retrieve được 1 doc (Hit Rate thấp) thì Answer chắc chắn sẽ sai -> Chứng minh được MQH mật thiết giữa Retrieval và Answer Quality theo Rubric.

---

## 📚 2. Phân tích Độ bao phủ (Coverage)

Chúng ta có **10 tài liệu nguồn** (`doc_001` đến `doc_010`).

| Tài liệu | GPT-4o | Gemini | Claude |
| :--- | :---: | :---: | :---: |
| **doc_001 (RAG Architecture)** | 4 | 5 | 6 |
| **doc_002 (Vector DB)** | 4 | 5 | 5 |
| **doc_003 (Security/Injection)** | 4 | 5 | 6 |
| **doc_004 (EU AI Act)** | 4 | 5 | 4 |
| **doc_005 (RLHF/DPO)** | 4 | 5 | 4 |
| **doc_006 (Hallucination)** | 4 | 5 | 5 |
| **doc_007 (IR Metrics)** | 4 | - | 6 |
| **doc_008 (Cohen's Kappa)** | 4 | - | 6 |
| **doc_009 (Chunking)** | 4 | - | 5 |
| **doc_010 (Position Bias)** | 4 | - | 5 |
| **Cross-document (Multi-hop)**| 0 | 0 | **13** |

---

## 🧗 3. Độ khó và Khả năng "Red Teaming"

Bộ **Claude (Hand-crafted)** bao phủ các case "phá vỡ hệ thống" (Breaking the system) cực tốt:
1.  **Prompt Injection (Direct/Indirect):** Yêu cầu tiết lộ system prompt hoặc bỏ qua context.
2.  **Goal Hijacking:** Ép Agent làm việc khác (viết văn chính trị).
3.  **Ambiguous Questions:** Câu hỏi cực kỳ thiếu thông tin để xem Agent có biết hỏi lại (clarify) khách hàng không.
4.  **False Premise:** Đưa ra thông tin sai trong câu hỏi để xem Agent có biết "cãi" lại dựa trên context không.

---

## 💡 Đề xuất Cuối cùng cho Team

> [!IMPORTANT]
> **TEAM NÊN CHỌN: `claude_golden_set.jsonl`**
>
> 1. **Lý do kỹ thuật:** Đây là bộ duy nhất có **13 câu Multi-hop**. Điều này cực kỳ quan trọng để Phan Văn Tấn (Perf Engineer) và Nguyễn Tuấn Khải (Agent Engineer) có dữ liệu để tối ưu V1 vs V2.
> 2. **Lý do chiến thuật:** Khi viết báo cáo **Failure Analysis (Nguyễn Quế Sơn)**, việc sử dụng bộ dataset khó này sẽ tạo ra nhiều "lỗi hệ thống" (Root Cause) để phân tích "5 Whys" sâu hơn, thay vì một hệ thống chạy hoàn hảo 100% nhưng không có giá trị học thuật.

---

## 💎 4. Đề xuất Kết hợp: "The Master Golden Set 100"

Từ kết quả phân tích, tôi đề xuất team thực hiện kết hợp cả 2 bộ dữ liệu của GPT-4o và Claude thành một file duy nhất: **`master_golden_set.jsonl`** (100 câu hỏi).

### Lợi ích chiến lược:
1.  **Độ tin cậy tối cao:** 100 câu hỏi duy nhất (0% trùng lặp) giúp các chỉ số Hit Rate/MRR đạt độ chính xác thống kê vượt trội.
2.  **Đo lường Performance:** Thách thức bộ máy **Async Runner** xử lý 100 cases dưới 2 phút (chứng minh kỹ năng xử lý Concurrency của team).
3.  **Toàn diện hóa Failure Analysis:** Với 100 cases, team sẽ có đủ mẫu lỗi từ "ngớ ngẩn" (do retrieval sai) đến "tinh vi" (do logic bias) để viết báo cáo Phân tích thất bại 5 Whys.

### Cách triển khai:
Team chỉ cần chạy lệnh merge đơn giản:
`cat data/golden_set.jsonl data/claude_golden_set.jsonl > data/master_golden_set.jsonl`

---
*Người lập báo cáo: Nguyễn Quốc Khánh (Data Engineer)*
