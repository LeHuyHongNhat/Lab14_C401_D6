# Reflection: Async Performance & Evaluation
**Tác giả:** Phan Văn Tấn
**Vai trò:** Async Performance Engineer

## 1. MRR là gì — ví dụ cụ thể với số liệu
MRR (Mean Reciprocal Rank) là chỉ số đo lường thứ hạng của tài liệu đúng đầu tiên được truy xuất. Nó trung bình hóa nghịch đảo của thứ hạng (rank) qua nhiều truy vấn.
Công thức: $MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{rank_i}$

**Ví dụ:**
- Truy vấn 1: Tài liệu đúng nằm ở top 1 -> Rank = 1, Reciprocal Rank (RR) = 1/1 = 1.0
- Truy vấn 2: Tài liệu đúng nằm ở top 3 -> Rank = 3, RR = 1/3 ≈ 0.33
- Truy vấn 3: Không tìm thấy tài liệu đúng trong top K -> RR = 0.0
=> MRR = (1.0 + 0.33 + 0.0) / 3 = 0.44

## 2. Tại sao Retrieval Quality → Answer Quality
Chất lượng của bước truy xuất (Retrieval Quality - đo bằng Hit Rate, MRR) ảnh hưởng trực tiếp tới chất lượng câu trả lời (Answer Quality).
- LLM không có thông tin nội bộ về các tài liệu doanh nghiệp. Nó phải dựa hoàn toàn vào Context đưa vào.
- **Nếu Retrieval rỗng (Hit Rate = 0):** LLM dễ bị ảo giác (hallucination) hoặc trả lời sai.
- **Nếu Retrieval nhiễu (MRR thấp):** Tài liệu đúng bị đẩy xuống dưới cùng. LLM có giới hạn về Context Window và "Lost in the Middle" (bỏ sót thông tin ở giữa), do đó tài liệu ở trên cùng (Rank cao) có trọng số lớn hơn khi generate câu trả lời.
- Bằng chứng: Khi chạy thử nghiệm, các test case có Hit Rate cao thường nhận điểm final_score từ LLM-as-a-Judge cao hơn hẳn.

## 3. asyncio.gather vs asyncio.Semaphore
- **asyncio.gather:** Dùng để chạy đồng thời nhiều coroutines cùng một lúc. Tuy nhiên, nó sẽ cố gắng khởi chạy TẤT CẢ các task ngay lập tức. Nếu có 1000 tasks, nó sẽ mở 1000 kết nối, có thể gây quá tải server, hết bộ nhớ hoặc bị API Rate Limit (HTTP 429).
- **asyncio.Semaphore:** Đóng vai trò như một "nhân viên gác cửa", giới hạn số lượng coroutines được phép chạy đồng thời tại một thời điểm (Concurrency Limit).
=> **Khi nào dùng cái gì:** Thường dùng kết hợp. Dùng `Semaphore` bên trong từng task để kiểm soát số luồng chạy thực tế, và truyền tất cả các tasks đó vào `asyncio.gather` để gom kết quả lại. Trong dự án này, Semaphore(5) đảm bảo gọi LLM API không quá 5 requests/giây để tránh Rate Limit.

## 4. 3 cách giảm 30% chi phí eval mà không giảm accuracy
1. **Dùng mô hình nhỏ hơn (như gpt-4o-mini, gemini-flash) cho các metrics đơn giản:** Faithfulness hoặc Relevancy có thể dùng model nhỏ thay vì GPT-4/Claude 3.5 Sonnet.
2. **Caching:** Lưu trữ kết quả Eval (hoặc kết quả sinh) theo bộ hash của `(Câu hỏi, Context, Trả lời)`. Nếu test case không đổi, lấy lại kết quả từ cache thay vì gọi lại Judge API.
3. **Adaptive Evaluation:** Thay vì gọi Multi-Judge cho 100% data, chỉ dùng Multi-Judge cho những test cases có sự chênh lệch (ví dụ mô hình nhỏ chấm điểm mâu thuẫn). Các cases mà model nhỏ tự tin cao có thể bỏ qua Multi-Judge để tiết kiệm.
