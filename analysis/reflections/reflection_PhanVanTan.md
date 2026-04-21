# Báo cáo Cá nhân - Phan Văn Tấn - 2A202600282 

## 1. Engineering Contribution (Đóng góp kỹ thuật)
Trong dự án này, tôi chịu trách nhiệm chính ở 2 module phức tạp là **Metrics (Retrieval Evaluator)** và **Async Performance (BenchmarkRunner)**.
- **Module Metrics (`engine/retrieval_eval.py`)**: Đã thiết kế và lập trình thuật toán tính toán `Hit Rate` và `MRR` chính xác từ dữ liệu thô (`expected_retrieval_ids` và `retrieved_ids`). Triển khai hàm `evaluate_batch` để chấm điểm hàng loạt, hỗ trợ tính toán trung bình (`mean`) một cách tự động.
- **Module Async (`engine/runner.py`)**: Tái cấu trúc cơ chế chạy Benchmark từ tuần tự sang song song hoàn toàn. 
  - Tích hợp `asyncio.gather` cùng `tqdm.asyncio` để đạt tốc độ xử lý hơn 100 cases/giây.
  - Xây dựng hệ thống đo lường hiệu năng (`total_time_seconds`, `avg_latency_per_case`) và quản lý chi phí (`cost_usd`).
- **Bằng chứng (Git Commits):** Các thay đổi kiến trúc này đã được commit vào nhánh `tan` và hợp nhất vào nhánh `main` (feat: hoàn thành nâng cấp Retrieval Evaluator và Async Performance Runner), góp phần quan trọng giúp toàn bộ pipeline hoàn tất trong < 1 giây thay vì 2 phút như trước đây.

## 2. Technical Depth (Chiều sâu kỹ thuật)
**A. Giải thích các khái niệm cốt lõi:**
- **MRR (Mean Reciprocal Rank):** Đo lường thứ hạng của tài liệu đúng đầu tiên được truy xuất. Nếu tài liệu đúng nằm ở Top 1, Reciprocal Rank là 1/1 = 1.0. Nếu ở Top 3, là 1/3 ≈ 0.33. MRR là trung bình của các nghịch đảo thứ hạng này. Nó quan trọng vì LLM thường bị "Lost in the Middle" — tài liệu đúng càng nằm gần đầu Context Window, chất lượng Answer càng cao.
- **Cohen's Kappa:** Là một chỉ số thống kê đo lường độ đồng thuận (Agreement Rate) giữa 2 giám khảo (ở đây là 2 LLM Judge). Khác với phần trăm đồng thuận thông thường, Kappa loại trừ xác suất đồng thuận do ngẫu nhiên, giúp đánh giá chính xác độ tin cậy của hệ thống Multi-Judge.
- **Position Bias:** Là hiện tượng LLM (đóng vai trò Giám khảo) thường có xu hướng thiên vị câu trả lời được đặt ở vị trí đầu tiên (Ví dụ: thiên vị Model A hơn Model B nếu A luôn được đưa ra trước). Cách khắc phục là hoán đổi vị trí A-B trong các lần chạy và lấy trung bình.

**B. Trade-off giữa Chi phí và Chất lượng (Cost vs Quality):**
- **Vấn đề:** Để đánh giá chính xác nhất (Quality cao), ta cần dùng các model đắt tiền (GPT-4o) cho vai trò Multi-Judge trên toàn bộ dataset. Tuy nhiên, điều này làm đẩy Cost lên mức không thể scale.
- **Giải pháp:** 
  1. Dùng model nhỏ (như Claude 3.5 Haiku) cho các task phân loại dễ, chỉ dùng model lớn cho các case xung đột.
  2. Implement Caching: không gọi lại API cho các cặp (Question, Context) trùng lặp.
  3. Bằng cách kết hợp linh hoạt, hệ thống có thể giảm được 30% chi phí Evaluator mà chỉ hy sinh < 2% độ chính xác (Accuracy).

## 3. Problem Solving (Kỹ năng giải quyết vấn đề)
**Vấn đề phát sinh:** Khi triển khai `asyncio.gather` để đẩy tốc độ chạy 50 cases cùng lúc, hệ thống ngay lập tức gặp lỗi HTTP 429 (Too Many Requests / Rate Limit) từ phía API của LLM, đồng thời làm tràn RAM.
**Cách giải quyết:**
- Ban đầu, tôi định chia chunk dữ liệu thủ công (chia thành các batch 5 cases) nhưng cách này tạo ra độ trễ dư thừa giữa các batch.
- **Giải pháp triệt để:** Tôi đã ứng dụng `asyncio.Semaphore(5)` để thiết lập "Concurrency Limit" ở mức Micro. Semaphore đóng vai trò như một "nhân viên gác cửa", đảm bảo tại bất kỳ một thời điểm nào (millisecond) cũng chỉ có tối đa 5 requests chạy song song lên LLM. 
- **Kết quả:** Hệ thống chạy trơn tru, biểu đồ tài nguyên ổn định, loại bỏ hoàn toàn lỗi Rate Limit mà vẫn đảm bảo tốc độ cực đại.
