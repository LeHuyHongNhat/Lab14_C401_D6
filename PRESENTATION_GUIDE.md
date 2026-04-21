# 🚀 Presentation Guide: Lab 14 — AI Evaluation Factory
## Hệ thống Đánh giá Tự động Đa mô hình (Multi-Judge Consensus Engine)

---

## 1. Giới thiệu tổng quan (The "Why")
**Vấn đề:** Đánh giá chất lượng RAG Agent bằng con người rất chậm, đắt và không khách quan. Ngược lại, chỉ dùng 1 LLM duy nhất làm giám khảo (LLM-as-Judge) thường bị sai lệch (bias).
**Giải pháp:** Xây dựng một "Nhà máy đánh giá" (Evaluation Factory) sử dụng **Hai giám khảo AI độc lập** (GPT-4o & Gemini) kết hợp với các chỉ số toán học chuẩn công nghiệp.

---

## 2. Kiến trúc hệ thống (System Architecture)

Hệ thống được chia thành 3 lớp cốt lõi:
1.  **Lớp Agent (The Candidate):** Một Agent RAG sử dụng `gpt-4o-mini` để trả lời câu hỏi dựa trên dữ liệu doanh nghiệp.
2.  **Lớp Đánh giá (Expert Evaluator):** 
    *   Tính toán **Hit Rate** và **MRR** (Mean Reciprocal Rank) để đo chất lượng tìm kiếm (Retrieval).
    *   Tự động so sánh ID tài liệu được lấy ra với ID chuẩn (Golden Set).
3.  **Lớp Giám khảo (Multi-Model Judge):** 
    *   Gọi song song **GPT-4o** và **Gemini 3.1 Pro/2.5 Pro**.
    *   Sử dụng Rubric chung (Accuracy, Professionalism, Hallucination-free).

---

## 3. Các tính năng kỹ thuật "Wow" (Technical Highlights)

### 3.1. Độ đồng thuận thông minh (Quadratic Weighted Kappa)
Chúng ta không chỉ đếm xem 2 model có cho điểm giống nhau không. Chúng ta dùng **QWK**:
*   Phạt nặng các trường hợp "trống đánh xuôi, kèn thổi ngược" (lệch nhiều điểm).
*   Tính toán xác suất trùng hợp ngẫu nhiên để đưa ra chỉ số **Agreement Rate** thực tế.

### 3.2. Cơ chế Tie-Breaker (Xử lý xung đột)
Nếu GPT cho 1 điểm mà Gemini cho 5 điểm? Hệ thống sẽ tự động kích hoạt **Tie-breaker**:
*   Gọi một model thứ 3 (hoặc GPT với prompt suy luận sâu hơn).
*   Yêu cầu giải thích chi tiết lý do thay đổi điểm.
*   Đảm bảo `final_score` luôn công bằng.

### 3.3. Phát hiện Thiên vị Vị trí (Position Bias Detection)
LLM thường thiên vị câu trả lời đứng đầu. 
*   **Giải pháp:** Hệ thống thực hiện đánh giá đảo ngược (A vs B rồi B vs A).
*   Nếu kết quả thay đổi → Hệ thống gắn cờ **Position Bias Detected**.

### 3.4. Xử lý tải cao (High-Performance Async)
*   Sử dụng `asyncio.Semaphore` để giới hạn số lượng request đồng thời.
*   Cơ chế **Exponential Backoff**: Tự động thử lại khi gặp lỗi `RateLimitError (429)`.
*   Tốc độ: Đánh giá 130 cases chỉ trong ~2 phút.

---

## 4. Release Gate & Regression Test (Quy trình ra mắt)

Đây là thành phần then chốt để đưa AI vào Production. Mỗi bản cập nhật (V2) phải đi qua **Gate**:
*   **APPROVE:** Điểm tăng, chi phí giảm, Hit Rate ổn định.
*   **WARN:** Có cải tiến nhưng chi phí tăng cao hoặc có rủi ro nhỏ.
*   **BLOCK:** Chất lượng bị tụt giảm (Regression spotted) → Ngăn chặn việc Deploy bản lỗi.

---

## 5. Kết luận & Demo Kết quả

*   **Kết quả:** Hệ thống tạo ra 3 báo cáo JSON chi tiết: `summary.json`, `benchmark_results.json`, `regression_report.json`.
*   **Giá trị:**
    *   Giảm 95% thời gian đánh giá model.
    *   Đo lường được chính xác ROI (Return on Investment) thông qua Cost Tracking.
    *   Đảm bảo tính tuân thủ (Compliance) cho các dự án AI doanh nghiệp.

---

## 💡 Gợi ý kịch bản thuyết trình (Presentation Script)

1.  **Mở đầu (1 phút):** Nêu thực trạng việc đánh giá AI hiện nay khó khăn như thế nào. Giới thiệu tên dự án "AI Evaluation Factory".
2.  **Kỹ thuật (2 phút):** Mở code `engine/llm_judge.py`, giải thích về công thức **Kappa** và cách xử lý **Gemini fallback**. Đây là phần ăn điểm về kỹ thuật chuyên sâu.
3.  **Pipeline (1 phút):** Mở `main.py`, giải thích về **Release Gate** và cách nó bảo vệ hệ thống không bị deploy "nhầm" bản kém chất lượng.
4.  **Kết quả (1 phút):** Show biểu đồ hoặc file `summary.json` vừa chạy xong. Nhấn mạnh vào việc hệ thống tự động đưa ra quyết định **APPROVE**.
5.  **Q&A:** Sẵn sàng trả lời về cách xử lý lỗi 429 và tại sao chọn 2 model này (GPT + Gemini).
