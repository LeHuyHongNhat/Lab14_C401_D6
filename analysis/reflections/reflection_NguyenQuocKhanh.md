# 📄 Personal Reflection - Nguyễn Quốc Khánh (Data Engineer / SDG Lead)

Nguyễn Quốc Khánh - 2A202600199

## 1. Engineering Contribution & Problem Solving
Trong Lab 14, vai trò chính của tôi là Data Engineer phụ trách module Synthetic Data Generation (SDG) để tạo Golden Dataset. 
- **Thiết kế & Tích hợp:** Tôi đã xây dựng `data/synthetic_gen.py`, thiết kế chuẩnschema JSONL chứa `expected_retrieval_ids` và hỗ trợ đa Engine (OpenAI & Gemini Vertex AI).
- **Xử lý sự cố (Problem Solving):** Khi sử dụng Gemini 2.5 Pro, hệ thống liên tục gặp lỗi `429 Resource Exhausted`. Tôi đã giải quyết bằng cách áp dụng **Semaphore(1) và Exponential Backoff (retry 5 lần)**. Tuy nhiên, khi nhận thấy giới hạn Quota của hệ thống quá nghiêm ngặt, gây "treo" quá trình sinh dữ liệu ở 30 cases, tôi đã linh hoạt xoay chuyển chiến thuật: chủ động thiết kế bộ **Claude Hand-crafted Dataset (50 cases)** đạt chuẩn Expert.
- **Tối ưu hóa chiến lược:** Đề xuất và chứng minh được phương án kết hợp không trùng lặp thành **Master Golden Set 100**, cung cấp đủ dữ liệu đa dạng (Multi-hop, Adversarial) để team thực hiện các Test phức tạp và viết báo cáo 5 Whys. Đóng góp minh chứng mảng Git qua các commit `feat(data)...`.

## 2. Technical Depth: Đánh giá & Metric
- **Vai trò của `expected_retrieval_ids`:** Đây là trường bắt buộc (Ground Truth) để tính toán tự động **Hit Rate** và **MRR (Mean Reciprocal Rank)**. Without it, hệ thống không thể biết Agent có truy xuất đúng tài liệu hay không, mà chỉ có thể đánh giá Answer Output (RAG không retrieval eval là vô nghĩa). MRR giúp đánh giá thứ hạng nội dung được lấy ra thay vì chỉ kiểm tra "có/không" như Hit Rate.
- **Red Teaming trong SDG:** Là kỹ thuật đưa các kịch bản khó (Prompt Injection, Goal Hijacking, Edge Cases) vào dataset để "stress-test" RAG Agent. Nếu thiếu Red Teaming, model có thể dễ dàng pass các case Fact-Check nhưng lại sụp đổ (Hallucination hoặc lộ lọt bảo mật) khi chạy thực tế.
- **Trade-off Cost vs Quality:** Qua việc tích hợp Vertex AI và OpenAI, tôi nhận thấy có sự đánh đổi giữa Model mạnh (đắt, chính xác, nhưng dễ chạm API Limit/Latency cao) và Model nhẹ. Việc gặp lỗi 429 là minh chứng thực tế cho bài toán vận hành hệ thống NLP quy mô lớn.
- **Circular Evaluation Problem:** Dùng LLM (GPT-4o) tạo câu hỏi, rồi lại dùng LLM (Claude/GPT) làm Judge dễ dẫn đến "self-enhancement bias" (tự thiên vị) hoặc các LLM chia sẻ chung điểm mù. Để giải quyết, tôi đã can thiệp tạo bộ **Claude Hand-crafted** bao gồm các câu **Multi-hop cross-doc** dựa trên thực tế, đảm bảo Ground Truth có sự kiểm chứng từ yếu tố con người.
- **Cohen's Kappa & Position Bias:** Khi team dùng Judge chấm, **Cohen's Kappa** giúp loại bỏ tỷ lệ đồng thuận ngẫu nhiên giữa 2 model, mang lại độ tin cậy thực tế cao hơn (vd: từ 78% xuống còn Kappa 0.52). Trong khi đó, **Position Bias** làm LLM Judge có xu hướng cho điểm cao hơn đối với đáp án nào xuất hiện trước, đòi hỏi phải swap vị trí để tính trung bình.

## 3. Tổng kết
Việc xây dựng hệ thống SDG giúp tôi hiểu rõ: Dữ liệu Test quyết định "trần" chất lượng của hệ thống RAG. Một bộ Test Case quá hiền sẽ ru ngủ team dev, trong khi bộ Master Golden Set 100 với Red Teaming tinh vi thực sự tạo ra sức ép để Agent và Evaluator phải được nâng cấp đúng nghĩa.
