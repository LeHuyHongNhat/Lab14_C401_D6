# Báo Cáo Cá Nhân - Lê Công Thành - 2A202600091

## 1. Vai trò và phạm vi đóng góp
- Vai trò chính: DevOps / Regression Gate Engineer.
- File chính phụ trách: `main.py`.
- Mục tiêu phần việc: so sánh V1 vs V2, quyết định release gate tự động, và đảm bảo report đầu ra đúng schema để checker chấp nhận.

## 2. Engineering Contribution
Trong `main.py`, tôi đã triển khai và hoàn thiện các phần sau:
- Xây dựng hàm `_release_gate(v1, v2)` với logic multi-criteria:
  - `APPROVE` nếu `score_delta >= 0` AND `cost_delta <= 0.1` AND `hit_rate_delta >= -0.05`.
  - `BLOCK` nếu `score_delta < -0.2` OR `hit_rate_delta < -0.1`.
  - `WARN` cho các trường hợp còn lại.
- Tổ chức benchmark hai phiên bản agent trong cùng một luồng chạy:
  - `Agent_V1_Base`
  - `Agent_V2_Optimized`
- Tổng hợp metric retrieval và judge vào summary:
  - `avg_score`, `hit_rate`, `mrr`, `agreement_rate`, `total_cost_usd`.
- Ghi đầy đủ 3 artifacts để nộp bài:
  - `reports/summary.json`
  - `reports/benchmark_results.json`
  - `reports/regression_report.json`
- Gắn metadata regression vào summary của V2 để phục vụ submission gate.

## 3. Kết quả thực tế từ reports
Dữ liệu dưới đây được trích trực tiếp từ `reports/summary.json` và `reports/regression_report.json`.

### 3.1 Kết quả V1
- total cases: 50
- avg_score: 4.6217
- hit_rate: 0.98
- mrr: 0.96
- agreement_rate: 0.9436
- total_cost_usd: 0.1203
- total_time_seconds: 44.1
- avg_latency_per_case: 1.99

### 3.2 Kết quả V2
- total cases: 50
- avg_score: 4.505
- hit_rate: 0.98
- mrr: 0.9433
- agreement_rate: 0.9178
- total_cost_usd: 0.1134
- total_time_seconds: 51.18
- avg_latency_per_case: 2.05

### 3.3 Delta và quyết định Regression Gate
- score_delta: -0.1167
- hit_rate_delta: 0.0
- mrr_delta: -0.0167
- cost_delta: -0.0069
- decision: WARN
- reasons:
  - Score giảm -0.117
  - Hit Rate tăng +0.000
  - Cost giảm 0.006900 USD

Nhận xét ngắn gọn:
- V2 tiết kiệm chi phí hơn V1.
- Tuy nhiên chất lượng điểm judge và MRR giảm.
- Hệ thống đưa ra WARN là phù hợp với gate đã đặt.

## 4. Technical Depth
### 4.1 Regression testing trong AI/ML khác software testing truyền thống ở điểm nào?
- Software testing truyền thống thường pass/fail theo rule cố định.
- AI/ML regression testing cần theo dõi metric liên tục (`score`, `retrieval`, `agreement`, `cost`, `latency`) và phải chấp nhận trade-off.
- Vì vậy không thể đánh giá release chỉ bằng 1 metric duy nhất.

### 4.2 Vì sao cần multi-criteria release gate
- Nếu chỉ nhìn `avg_score`, có thể bỏ qua bài toán chi phí vận hành.
- Nếu chỉ nhìn `cost`, có thể release model rẻ nhưng kém chất lượng.
- Multi-criteria gate giảm rủi ro khi deploy, vì cân bằng chất lượng retrieval, chất lượng answer và chi phí.

### 4.3 Goodhart's Law trong ngữ cảnh bài lab
Goodhart's Law: khi một chỉ số trở thành mục tiêu tối ưu, nó không còn là chỉ số đánh giá tốt nữa.
- Nếu tối ưu cực đoan cho 1 metric (ví dụ chỉ score judge), hệ thống có thể xấu đi ở metric khác (chi phí, latency, retrieval rank).
- Release gate được đặt để hạn chế tình huống này bằng cách đánh giá đồng thời nhiều metric.

## 5. Problem Solving
### Vấn đề 1: Xác định ngưỡng gate để tránh kết luận sai
- Nếu ngưỡng quá chặt dễ dẫn đến BLOCK oan.
- Nếu ngưỡng quá lỏng dễ dẫn đến APPROVE model kém.
- Cách giải quyết: dùng 3 mức `APPROVE/WARN/BLOCK` thay vì nhị phân, giúp quyết định an toàn hơn.

### Vấn đề 2: Đảm bảo output phục vụ nộp bài
- Bài lab yêu cầu report phải có metadata + metrics rõ ràng.
- Cách giải quyết: bổ sung thông tin regression vào `reports/summary.json`, đồng thời tạo `reports/regression_report.json` để giải trình delta.

### Vấn đề 3: Đồng bộ kết quả benchmark và checker
- Mục tiêu là pipeline chạy xong và checker pass.
- Kết quả thực tế: lệnh `python check_lab.py` đã pass trong môi trường chạy hiện tại.

## 6. Định hướng tích hợp CI/CD
Nếu mở rộng sau lab, tôi đề xuất tích hợp gate này vào CI:
- Trigger khi có PR thay đổi agent/judge/retrieval.
- Pipeline tự động chạy benchmark V1 vs V2 trên cùng dataset.
- Đọc `reports/regression_report.json` và enforce policy:
  - `APPROVE`: merge được.
  - `WARN`: cần review thủ công trước khi merge.
  - `BLOCK`: fail check, không cho merge.

## 7. Tự đánh giá theo rubric cá nhân
- Engineering Contribution: đã có đóng góp trực tiếp vào main orchestration và release gate.
- Technical Depth: giải thích được trade-off quality-cost và lý do cần multi-criteria.
- Problem Solving: xử lý bài toán quyết định release trong điều kiện metric xung đột.

Tổng kết: Phần việc cá nhân của tôi đạt đúng trọng tâm rubric Regression Testing và đóng vai trò cầu nối giữa benchmark kết quả và quyết định phát hành model.