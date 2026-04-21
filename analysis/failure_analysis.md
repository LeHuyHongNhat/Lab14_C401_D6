# Báo cáo Phân tích Lỗi (Failure Analysis Report)
---
**Dự án:** AI Evaluation Factory - Hệ thống Đánh giá Tự động RAG  
**Người thực hiện:** Nguyễn Quế Sơn  
**Vai trò:** Chuyên gia Phân tích Thất bại (Analyst / 5 Whys Expert)  
**Ngày báo cáo:** 21 tháng 04 năm 2026

## 1. Tổng quan Benchmark & Quy trình Phân tích
Báo cáo này đại diện cho kết quả phân tích cuối cùng sau khi hệ thống đã được tích hợp toàn bộ các module kỹ thuật từ tất cả thành viên trong nhóm. Mục tiêu của báo cáo là không chỉ chỉ ra các điểm yếu hiện tại của Agent V2 mà còn cung cấp một lộ trình (Roadmap) kỹ thuật để đạt được sự hoàn hảo trong phiên bản V3.

### 1.1. Thông số Kỹ thuật
- **Tập dữ liệu:** 50 cases (Gold Standard Dataset).
- **Mô hình Judge:** Hệ thống Multi-Judge (GPT-4o + Gemini).
- **Kết quả V1 (Baseline):** 4.62/5.0 | Hit Rate: 0.98 | MRR: 0.960
- **Kết quả V2 (Optimized):** 4.51/5.0 | Hit Rate: 0.98 | MRR: 0.943
- **Agreement Rate:** 0.918
- **Quyết định Release Gate:** **WARN** ⚠️ (V2 có score thấp hơn V1 nhưng chi phí giảm, Hit Rate giữ nguyên).

### 1.2. Phương pháp luận
Chúng tôi sử dụng phương pháp **5 Whys (Năm câu hỏi Tại sao)** để truy vết từ triệu chứng bề mặt (Symptom) đến nguyên nhân gốc rễ (Root Cause) trong kiến trúc hệ thống RAG (Retrieval-Augmented Generation).

---

## 2. Phân loại Lỗi (Failure Clustering)
Dựa trên kết quả Benchmark, chúng tôi phân loại các thất bại của hệ thống vào các nhóm lỗi thực tế sau:

| Nhóm Lỗi | Số lượng | Tỉ lệ (%) | Mô tả Triệu chứng thực tế |
| :--- | :---: | :---: | :--- |
| **Temporal Hallucination** | 1 | 3.3% | Nhầm lẫn giữa các mốc thời gian thực thi pháp lý khác nhau trong context. |
| **Granularity Mismatch** | 2 | 6.7% | Trả lời đúng ý chính nhưng thiếu các chi tiết định lượng cụ thể mà Judge yêu cầu. |
| **Conciseness Over-tuning** | 1 | 3.3% | Câu trả lời quá ngắn gọn dẫn đến việc bỏ lỡ các sắc thái (nuances) quan trọng. |
| **Success Cases** | 26 | 86.7% | Agent trả lời hoàn hảo, khớp hoàn toàn với Ground Truth. |

---

## 3. Phân tích 5 Whys cho các Case tiêu biểu

### Case #1: EU AI Act Biometric Ban (Score 1.5/5.0)
*Đây là case có điểm thấp nhất, phản ánh lỗi logic phức tạp.*

- **Triệu chứng (Symptom):** Agent khẳng định đạo luật EU AI Act cấm hoàn toàn nhận diện khuôn mặt thời gian thực ngay tại thời điểm hiện tại.
- **Tại sao 1:** LLM đã đưa ra kết luận dựa trên một đoạn văn bản nói về "Prohibited AI practices" mà không xét đến lộ trình thực thi.
- **Tại sao 2:** Context cung cấp cho LLM chứa quá nhiều mốc thời gian rải rác (Tháng 8/2024, Tháng 2/2025, Năm 2026) làm mô hình bị nhiễu thông tin.
- **Tại sao 3:** Hệ thống Retrieval (Top-K=3) đã lấy ra các chunks chứa thông tin về lệnh cấm nhưng không lấy được chunk chứa thông tin về "Grace period" (thời gian ân hạn).
- **Tại sao 4:** Kỹ thuật Chunking hiện tại (Fixed-size 500 tokens) đã vô tình cắt ngang đoạn văn bản giải thích về các ngoại lệ của luật.
- **Tại sao 5:** Hệ thống chưa có cơ chế **Semantic Chunking** để giữ các khối thông tin pháp lý đi liền với nhau.
- **👉 Nguyên nhân gốc rễ (Root Cause):** Chiến lược Chunking cố định làm đứt gãy tính logic của các văn bản có cấu trúc phân tầng phức tạp.

### Case #2: Performance Metrics GPT-4o vs Llama-3 (Score 4.0/5.0)
- **Triệu chứng:** Agent liệt kê đúng model nhưng thiếu các con số phần trăm (%) cụ thể về tỉ lệ Hallucination.
- **Tại sao 1:** LLM chỉ tóm tắt ý chính thay vì trích xuất dữ liệu thô.
- **Tại sao 2:** Prompt của V2 đang quá ưu tiên tính "Conciseness" (Ngắn gọn), làm mô hình hiểu lầm rằng không cần liệt kê số liệu chi tiết.
- **Tại sao 3:** System Prompt yêu cầu "Be concise: 2-4 sentences", giới hạn này quá chặt chẽ đối với các câu hỏi đòi hỏi báo cáo số liệu.
- **Tại sao 4:** Hệ thống chưa phân loại được Intent của người dùng (Question Classification) để điều chỉnh độ dài câu trả lời.
- **Tại sao 5:** Thiếu bước **Query Decomposition** để tách câu hỏi so sánh thành các tiểu mục nhỏ cần trích xuất dữ liệu.
- **👉 Nguyên nhân gốc rễ:** Xung đột giữa chỉ thị về phong cách (Style guidelines) và yêu cầu về độ chi tiết của thông tin (Information density).

### Case #3: RAG Definition Complexity (Score 4.5/5.0)
- **Triệu chứng:** Câu trả lời đúng nhưng bị Judge đánh giá là "hơi thiếu tính chuyên nghiệp trong cách trình bày".
- **Tại sao 1:** Cấu trúc câu trả lời là một đoạn văn liền mạch thay vì chia bullet points.
- **Tại sao 2:** LLM sử dụng ngôn ngữ quá phổ thông, thiếu các thuật ngữ chuyên ngành (Vector DB, Embedding, v.v.).
- **Tại sao 3:** Ngữ cảnh truyền vào Agent V2 bị cắt bớt để đảm bảo tốc độ, làm mất đi các thuật ngữ chuyên môn sâu trong tài liệu gốc.
- **Tại sao 4:** Tham số `top_k=3` của V2 đôi khi quá ít để bao quát toàn bộ định nghĩa từ nhiều góc độ khác nhau.
- **Tại sao 5:** Sự đánh đổi (Trade-off) giữa Latency (Tốc độ) và Richness (Sự phong phú của thông tin).
- **👉 Nguyên nhân gốc rễ:** Cấu hình tham số Retrieval (Top-K) chưa tối ưu cho các câu hỏi mang tính định nghĩa khái niệm rộng.

---

## 4. Kế hoạch Hành động (Action Plan) cho Agent V3

Để giải quyết triệt để các vấn đề nêu trên, tôi đề xuất 5 hạng mục cải tiến kỹ thuật cụ thể:

1. **Triển khai Semantic Chunking:** Thay thế Fixed-size chunking bằng Recursive Character Splitter kết hợp với AI để nhận diện ranh giới ngữ nghĩa của văn bản (Giải quyết lỗi Case #1).
2. **Dynamic Top-K Retrieval:** Phát triển module dự đoán độ phức tạp của câu hỏi. Nếu là câu hỏi "Comparison" hoặc "Legal", tự động tăng Top-K từ 3 lên 7 để tăng Recall (Giải quyết lỗi Case #3).
3. **Hybrid Reranking (BGE-Reranker):** Sử dụng mô hình Cross-Encoder để xếp hạng lại các chunks sau khi retrieve, đảm bảo các chunks có tính logic cao nhất được đưa lên đầu.
4. **Adaptive Prompting:** Điều chỉnh System Prompt để LLM biết khi nào cần "Concise" (câu hỏi Yes/No) và khi nào cần "Detailed" (câu hỏi thống kê/so sánh).
5. **Self-Correction Layer:** Thêm một bước kiểm tra phụ (Refinement step) nơi LLM tự đối chiếu câu trả lời của mình với context một lần nữa để phát hiện Hallucination trước khi trả kết quả cho người dùng.

---
*Báo cáo được trình bày bởi Nguyễn Quế Sơn nhằm mục đích phục vụ công tác nghiệm thu dự án Lab 14.*
