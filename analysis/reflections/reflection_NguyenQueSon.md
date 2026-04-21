# 🧠 Bài Thu hoạch Cá nhân (Reflection) - BẢN TÍCH HỢP CUỐI CÙNG
---
**Thành viên:** Nguyễn Quế Sơn - 2A202600198
**Vai trò:** Analyst / 5 Whys Expert

## 1. Trải nghiệm Tích hợp Hệ thống
- **Tôn trọng mã nguồn chung:** Trong giai đoạn cuối, tôi đã thực hiện hợp nhất toàn bộ mã nguồn từ nhánh `main` và các thành viên khác. Tôi đã học được cách giải quyết xung đột bằng cách ưu tiên logic của các "Expert" trong team (Nhật cho Judge, Tấn cho Runner, v.v.).
- **Tính thực tế:** Việc chạy Benchmark trên tập dữ liệu chính thức của nhóm (30 cases) cho thấy hệ thống đã đạt ngưỡng **APPROVE**. Điều này minh chứng cho sự nỗ lực chung của cả team trong việc tinh chỉnh Agent.

## 2. Bài học về Phân tích Lỗi
- **Sự khác biệt giữa các Dataset:** Tôi nhận thấy lỗi thay đổi hoàn toàn khi đổi tập dữ liệu. Với tập dữ liệu lớn (130 cases), lỗi chủ yếu là "No Info". Với tập dữ liệu tinh lọc của nhóm (30 cases), lỗi chỉ còn lại duy nhất là "Hallucination" liên quan đến logic thời gian.
- **Vai trò của Analyst:** Công việc của tôi không chỉ là tìm lỗi, mà là đảm bảo tính nhất quán của hệ thống sau mỗi lần tích hợp.

## 3. Đóng góp Kỹ thuật
- Tôi đã xây dựng script tự động hóa `analysis/clustering.py` giúp phân loại lỗi ngay lập tức sau mỗi lần chạy Benchmark.
- Tôi đã đảm bảo môi trường thực thi (Environment) luôn sẵn sàng bằng cách quản lý các biến môi trường và SDK cho toàn bộ team.

## 4. Tầm nhìn Mở rộng
- Nếu dự án tiếp tục, tôi sẽ đề xuất tích hợp **Automated Error Monitoring** trực tiếp vào Pipeline để mỗi khi một thành viên Push code mới, hệ thống sẽ tự động chạy Clustering và báo cáo 5 Whys cho các lỗi mới phát sinh.

---
*Hoàn tất tích hợp: 2026-04-21*
