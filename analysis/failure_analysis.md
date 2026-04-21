# 🕵️ Báo cáo Phân tích Lỗi (Failure Analysis Report) - BẢN TÍCH HỢP CUỐI CÙNG
---
**Dự án:** AI Evaluation Factory
**Người thực hiện:** Nguyễn Quế Sơn
**Ngày báo cáo:** 2026-04-21

## 1. Tổng quan Benchmark (Code chính thức từ Team)
Báo cáo này sử dụng toàn bộ mã nguồn mới nhất được hợp nhất từ `main` và các nhánh của thành viên (Nhật, Thành, Tấn, Khải, Khánh).

- **Dữ liệu test:** 30 cases (`gemini_golden_set.jsonl`)
- **Điểm trung bình V1:** 4.58
- **Điểm trung bình V2:** 4.77
- **Trạng thái:** **Cải thiện (Improvement)**. Trên tập dữ liệu 30 cases này, phiên bản V2 đã vượt qua V1.
- **Quyết định:** **APPROVE** ✅

## 2. Phân loại Lỗi (Failure Clustering)
Với code chính thức và tập dữ liệu thu nhỏ, hệ thống hoạt động cực kỳ ổn định, chỉ ghi nhận **1 case** bị điểm thấp:

| Nhóm Lỗi | Số lượng | Tỉ lệ (%) | Mô tả Triệu chứng |
| :--- | :---: | :---: | :--- |
| **Hallucination** | 1 | 100% | Nhầm lẫn về mốc thời gian thực thi của EU AI Act. |
| **Các nhóm khác** | 0 | 0% | Không ghi nhận lỗi. |

## 3. Phân tích 5 Whys (Root Cause Analysis)

### Case Duy nhất: EU AI Act Biometric Ban (Score 1.5)
- **Symptom:** Agent khẳng định EU AI Act cấm hoàn toàn nhận diện khuôn mặt thời gian thực ngay lập tức.
- **Why 1:** LLM trả lời dựa trên thông tin cũ hoặc suy luận sai từ context.
- **Why 2:** Context chứa nhiều mốc thời gian khác nhau (August 2024, May 2025, 2026) làm LLM bị nhiễu.
- **Why 3:** Hệ thống RAG lấy ra 3 chunks khác nhau về các giai đoạn thực thi nhưng không sắp xếp theo trình tự thời gian.
- **Why 4:** Agent V2 ưu tiên tính ngắn gọn (conciseness) nên đã bỏ qua các phần giải thích về "Exceptions" (ngoại lệ) trong luật.
- **Why 5:** LLM Judge (GPT-4o) phát hiện ra sự thiếu sót này và trừ điểm nặng vì tính "Accuracy".
- **👉 Root Cause:** Xung đột giữa chỉ thị "Conciseness" (Ngắn gọn) và yêu cầu "Accuracy" (Chính xác) trong các văn bản pháp luật phức tạp.

## 4. Tổng kết & Đề xuất
- **Đánh giá:** Code tích hợp của team đã giải quyết được phần lớn các lỗi nghiêm trọng trước đó. Sự kết hợp giữa Multi-Judge (GPT-4o + Gemini) giúp đánh giá công bằng và khắt khe hơn.
- **Đề xuất V3:** Mặc dù kết quả 30 cases rất tốt, nhưng để scale lên 1000 cases, team cần tối ưu hóa chi phí gọi Judge (hiện tại đang gọi song song 2-3 model lớn).
