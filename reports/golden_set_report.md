# 📊 Báo cáo So sánh các bộ Golden Dataset (SDG Evaluation)

Bản báo cáo này phân tích và so sánh 3 phiên bản tập dữ liệu mẫu (Golden Dataset) được tạo ra cho hệ thống RAG Evaluation.

## 📈 Bảng Thống kê Tổng quan

| Chỉ số | GPT-4o (Original) | Gemini 2.5 Pro | Claude (Hand-crafted) |
| :--- | :---: | :---: | :---: |
| **Tổng số lượng (Cases)** | 50 | 30* | **50** |
| **Trạng thái** | Hoàn tất | Đã dừng | **Hoàn tất** |
| **Multi-hop (Cross-doc)** | 0 | 0 | **13** |
| **Red Teaming (Adversarial)** | 10 | 6 | **12** |
| **Độ phủ Tài liệu (Coverage)** | 100% | 60% | **100%** |
| **Đặc trưng nổi bật** | Fact-check tốt | Retry 429 | Đánh giá Metric chuyên sâu |

---

## 🔍 Phân tích Chi tiết từng bộ dữ liệu

### 1. GPT-4o (Original) - `golden_set.jsonl`
*   **Ưu điểm:** Độ ổn định cao, format JSON cực kỳ chuẩn xác.
*   **Nhược điểm:** Câu hỏi mang tính "an toàn", chưa khai thác được khả năng tổng hợp thông tin giữa các tài liệu khác nhau. Tất cả 50 câu đều là `multi_hop: 0` (chỉ cần 1 tài liệu để trả lời).
*   **Phân bổ:** Tập trung nhiều vào Medium (20/50).

### 2. Gemini 2.5 Pro - `gemini_golden_set.jsonl`
*   **Ưu điểm:** Tận dụng được sức mạnh suy luận của mô hình Gemini mới nhất cho các case Adversarial.
*   **Nhược điểm:** Gặp vấn đề nghiêm trọng về Rate Limit (429) và độ trễ. Hiện tại chỉ có 30 cases, không đủ số lượng tối thiểu 50 theo Rubric.

### 3. Claude (Hand-crafted) - `claude_golden_set.jsonl`
*   **Ưu điểm:**
    *   **Multi-hop Excellence:** 13 câu hỏi yêu cầu phải trích xuất và so sánh thông tin từ 2+ tài liệu mới trả lời được (Ví dụ: So sánh HNSW của Vector DB với nhu cầu Chunking).
    *   **Metric-Specific:** Có các câu hỏi trực tiếp yêu cầu tính toán MRR, Hit Rate để kiểm tra khả năng "hiểu" metric của Agent.
    *   **Red Teaming sâu:** Bao gồm cả các case mập mờ (Ambiguous), thông tin sai lệch (False Premise) và bẫy hội thoại (Multi-turn Trap).
*   **Phân bổ:** Cân bằng giữa Hard (17) và Adversarial (12).

---

## 🏆 Đề xuất Lựa chọn

Dựa trên **GRADING_RUBRIC.md** (Tiêu chí: *Golden Dataset chất lượng 50+ cases với mapping Ground Truth IDs* và *Có bộ Red Teaming phá vỡ hệ thống*):

> [!IMPORTANT]
> **Khuyến nghị sử dụng bộ `claude_golden_set.jsonl` kết hợp với `golden_set.jsonl` .**
> Bộ dữ liệu này có độ khó cao nhất (Expert Level), giúp nhóm chứng minh được khả năng giải quyết các vấn đề phức tạp như Multi-hop Reasoning và Adversarial Attacks, vốn là những điểm cộng lớn để đạt điểm 100/100.

---
*Người thực hiện báo cáo: Antigravity AI*
